import json
import sys

import grpc
from google.protobuf import struct_pb2


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python grpc_client.py '<json_payload>'")

    payload = json.loads(sys.argv[1])
    addr = payload.get("addr", "127.0.0.1:50051")

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
        method = channel.unary_unary(
            "/wechatbot.WxAutoBridge/Chat",
            request_serializer=struct_pb2.Struct.SerializeToString,
            response_deserializer=struct_pb2.Struct.FromString,
        )
        resp = method(req, timeout=30)

    ok = resp.fields.get("ok", struct_pb2.Value(bool_value=False)).bool_value
    if not ok:
        err = resp.fields.get("error", struct_pb2.Value(string_value="unknown error")).string_value
        raise SystemExit(f"bridge returned error: {err}")


if __name__ == "__main__":
    main()
