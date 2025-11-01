from typing import Any
from google.protobuf.message import Message as ProtoMessage
from google.protobuf.json_format import MessageToDict
import proto
import datetime
from bson import ObjectId  # Import ObjectId

def _is_proto_plus_message(obj: Any) -> bool:
    """Checks if an object is a proto-plus message."""
    return isinstance(obj, proto.message.Message) if hasattr(proto, "message") else False

def safe_serialize(obj: Any) -> Any:
    """Recursively convert proto / proto-plus / protobuf / ObjectId objects to JSON-safe data."""
    if obj is None:
        return None
        
    # --- Fix for MongoDB BSON types ---
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime.datetime) or isinstance(obj, datetime.date):
        return obj.isoformat()
    # --- End of BSON fix ---

    # google.protobuf
    if isinstance(obj, ProtoMessage):
        return MessageToDict(obj, preserving_proto_field_name=True, use_integers_for_enums=True)
    
    # proto-plus
    try:
        if _is_proto_plus_message(obj):
            if hasattr(obj, "to_dict"):
                return obj.to_dict()
            if hasattr(obj, "as_dict"):
                return obj.as_dict()
            if hasattr(obj, "_pb"):
                return MessageToDict(obj._pb, preserving_proto_field_name=True)
    except Exception:
        pass
    
    # dict / list / tuple / set
    if isinstance(obj, dict):
        return {k: safe_serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [safe_serialize(v) for v in obj]
    
    # primitives
    if isinstance(obj, (str, int, float, bool)):
        return obj
    
    # fallback
    if hasattr(obj, "__dict__"):
        try:
            return safe_serialize(vars(obj))
        except Exception:
            pass
    try:
        return str(obj)
    except Exception:
        return None