import argparse
import logging
import os
import sys
from concurrent import futures
from typing import Any, Iterable

import grpc
from google.protobuf import struct_pb2


logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(message)s")


def _load_wxauto(project_root: str):
    wxauto_dir = os.path.join(project_root, "wxauto")
    if os.path.isdir(wxauto_dir):
        sys.path.insert(0, project_root)

    try:
        from wxauto import WeChat  # type: ignore
    except Exception as exc:  # noqa: BLE001
        logging.warning("wxauto import failed, fallback dry-run mode: %s", exc)
        return None
    return WeChat


class WxAutoAdapter:
    def __init__(self, project_root: str):
        self.WeChat = _load_wxauto(project_root)
        self._wx = None
        self._listen_targets: set[str] = set()

    def _instance(self):
        if self.WeChat is None:
            return None
        if self._wx is None:
            self._wx = self.WeChat()
        return self._wx

    def send_message(self, target_remark: str, text: str):
        wx = self._instance()
        if wx is None:
            logging.info("[dry-run] send to %s: %s", target_remark, text)
            return

        wx.ChatWith(target_remark)
        wx.SendMsg(text)

    def _extract_text(self, message_obj: Any) -> str:
        if isinstance(message_obj, str):
            return message_obj.strip()
        if isinstance(message_obj, dict):
            for key in ("content", "text", "msg", "message"):
                v = message_obj.get(key)
                if isinstance(v, str) and v.strip():
                    return v.strip()
            return str(message_obj).strip()

        for attr in ("content", "text", "msg", "message"):
            if hasattr(message_obj, attr):
                value = getattr(message_obj, attr)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return str(message_obj).strip()

    def _pick_last_text(self, messages: Iterable[Any]) -> str:
        items = list(messages)
        if not items:
            return ""
        for item in reversed(items):
            text = self._extract_text(item)
            if text:
                return text
        return ""

    def poll_latest_message(self, target_remark: str) -> str:
        wx = self._instance()
        if wx is None:
            return ""

        # Preferred: wxauto listen APIs
        if hasattr(wx, "AddListenChat") and hasattr(wx, "GetListenMessage"):
            if target_remark not in self._listen_targets:
                wx.AddListenChat(target_remark)
                self._listen_targets.add(target_remark)

            listened = wx.GetListenMessage()
            if isinstance(listened, dict):
                target_msgs = listened.get(target_remark)
                if target_msgs is None:
                    for _, msgs in listened.items():
                        text = self._pick_last_text(msgs if isinstance(msgs, list) else [msgs])
                        if text:
                            return text
                    return ""
                return self._pick_last_text(target_msgs if isinstance(target_msgs, list) else [target_msgs])

        # Fallback: switch to chat and fetch all history API if available
        wx.ChatWith(target_remark)
        if hasattr(wx, "GetAllMessage"):
            all_messages = wx.GetAllMessage()
            if isinstance(all_messages, list):
                return self._pick_last_text(all_messages)

        return ""


class BridgeService:
    def __init__(self, adapter: WxAutoAdapter):
        self.adapter = adapter
        self.last_seen: dict[str, str] = {}

    def chat(self, request: struct_pb2.Struct, context):
        fields = request.fields
        target = fields.get("target_remark", struct_pb2.Value(string_value="Zachary")).string_value
        user_message = fields.get("user_message", struct_pb2.Value(string_value="")).string_value
        reply = fields.get("reply", struct_pb2.Value(string_value="")).string_value

        text = f"{reply}"
        logging.info("incoming for %s | user=%s | reply=%s", target, user_message, reply)

        resp = struct_pb2.Struct()
        try:
            self.adapter.send_message(target, text)
            resp.update({"ok": True})
        except Exception as exc:  # noqa: BLE001
            logging.exception("send_message failed")
            resp.update({"ok": False, "error": str(exc)})
        return resp

    def poll(self, request: struct_pb2.Struct, context):
        fields = request.fields
        target = fields.get("target_remark", struct_pb2.Value(string_value="Zachary")).string_value

        resp = struct_pb2.Struct()
        try:
            latest = self.adapter.poll_latest_message(target)
            latest = latest.strip()

            if not latest:
                resp.update({"ok": True, "has_new": False, "message": ""})
                return resp

            if self.last_seen.get(target) == latest:
                resp.update({"ok": True, "has_new": False, "message": ""})
                return resp

            self.last_seen[target] = latest
            logging.info("new message for %s: %s", target, latest)
            resp.update({"ok": True, "has_new": True, "message": latest})
            return resp
        except Exception as exc:  # noqa: BLE001
            logging.exception("poll_latest_message failed")
            resp.update({"ok": False, "has_new": False, "error": str(exc)})
            return resp


def serve(host: str, port: int, project_root: str):
    adapter = WxAutoAdapter(project_root)
    service = BridgeService(adapter)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    handlers = {
        "Chat": grpc.unary_unary_rpc_method_handler(
            service.chat,
            request_deserializer=struct_pb2.Struct.FromString,
            response_serializer=struct_pb2.Struct.SerializeToString,
        ),
        "Poll": grpc.unary_unary_rpc_method_handler(
            service.poll,
            request_deserializer=struct_pb2.Struct.FromString,
            response_serializer=struct_pb2.Struct.SerializeToString,
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler("wechatbot.WxAutoBridge", handlers)
    server.add_generic_rpc_handlers((generic_handler,))

    bind_addr = f"{host}:{port}"
    server.add_insecure_port(bind_addr)
    server.start()
    logging.info("bridge server started at %s", bind_addr)
    server.wait_for_termination()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=50051)
    parser.add_argument("--project-root", default=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    args = parser.parse_args()
    serve(args.host, args.port, args.project_root)
