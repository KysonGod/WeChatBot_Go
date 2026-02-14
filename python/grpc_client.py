import json
import sys

import grpc
from google.protobuf import struct_pb2


def _call(channel, method_name: str, req: struct_pb2.Struct):
    method = channel.unary_unary(
        method_name,
        request_serializer=struct_pb2.Struct.SerializeToString,
        response_deserializer=struct_pb2.Struct.FromString,
    )
    return method(req, timeout=30)


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python grpc_client.py '<json_payload>'")

    payload = json.loads(sys.argv[1])
    addr = payload.get("addr", "127.0.0.1:50051")
    action = payload.get("action", "chat")

    req = struct_pb2.Struct()
    req.update(
        {
            "target_remark": payload.get("target_remark", "Zachary"),
            "persona": payload.get("persona", ""),
            "user_message": payload.get("user_message", ""),
            "reply": payload.get("reply", ""),
        }
    )

    with grpc.insecure_channel(addr) as channel:
        if action == "poll":
            resp = _call(channel, "/wechatbot.WxAutoBridge/Poll", req)
            ok = resp.fields.get("ok", struct_pb2.Value(bool_value=False)).bool_value
            if not ok:
                err = resp.fields.get("error", struct_pb2.Value(string_value="unknown error")).string_value
                raise SystemExit(f"bridge returned poll error: {err}")

            output = {
                "has_new": resp.fields.get("has_new", struct_pb2.Value(bool_value=False)).bool_value,
                "message": resp.fields.get("message", struct_pb2.Value(string_value="")).string_value,
            }
            print(json.dumps(output, ensure_ascii=False))
            return

        resp = _call(channel, "/wechatbot.WxAutoBridge/Chat", req)

    ok = resp.fields.get("ok", struct_pb2.Value(bool_value=False)).bool_value
    if not ok:
        err = resp.fields.get("error", struct_pb2.Value(string_value="unknown error")).string_value
        raise SystemExit(f"bridge returned error: {err}")

    print('{"ok": true}')


if __name__ == "__main__":
    main()
