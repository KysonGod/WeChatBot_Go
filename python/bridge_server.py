import argparse
import logging
import os
import sys
from concurrent import futures

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

        # wxauto common usage: ChatWith + SendMsg
        wx.ChatWith(target_remark)
        wx.SendMsg(text)


class BridgeService:
    def __init__(self, adapter: WxAutoAdapter):
        self.adapter = adapter

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


def serve(host: str, port: int, project_root: str):
    adapter = WxAutoAdapter(project_root)
    service = BridgeService(adapter)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    handlers = {
        "Chat": grpc.unary_unary_rpc_method_handler(
            service.chat,
            request_deserializer=struct_pb2.Struct.FromString,
            response_serializer=struct_pb2.Struct.SerializeToString,
        )
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
