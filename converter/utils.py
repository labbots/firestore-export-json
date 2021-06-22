from base64 import b64decode
import calendar
import datetime
from typing import Dict

from google.appengine.datastore import entity_bytes_pb2 as entity_pb2
from google.protobuf.json_format import MessageToDict


def get_dest_dict(key, json_tree):
    parent = key.parent()
    if parent is None:
        kind = key.kind()
        id_or_name = key.id_or_name()
        if kind not in json_tree:
            json_tree[kind] = {}
        if id_or_name not in json_tree[kind]:
            json_tree[kind][id_or_name] = {}
        return json_tree[kind][id_or_name]
    else:
        json_tree2 = get_dest_dict(key.parent(), json_tree)
        kind = key.kind()
        id_or_name = key.id_or_name()
        if kind not in json_tree2:
            json_tree2[kind] = {}
        if id_or_name not in json_tree2[kind]:
            json_tree2[kind][id_or_name] = {}
        return json_tree2[kind][id_or_name]


def get_value(value: Dict, raw=False):
    v = value.get("stringValue")
    if v:
        decoded_value = b64decode(v)
        return decoded_value if raw else decoded_value.decode("utf-8", errors="ignore")

    v = value.get("int64Value")
    if v:
        # not certain why, but without the cast to `int` here it shows up as a str in the output
        return int(v)

    return value.get("doubleValue", value.get("booleanValue"))


def embedded_entity_to_dict(embedded_entity, data):
    ep = entity_pb2.EntityProto()
    ep.ParseFromString(embedded_entity)
    d = MessageToDict(ep)
    for entry in d.get("rawProperty", []):
        name = entry.get("name")
        value = entry.get("value")
        if entry.get("meaning") == "ENTITY_PROTO":
            dt = {}
            data[name] = embedded_entity_to_dict(get_value(value, raw=True), dt)
        else:
            data[name] = get_value(value)
    return data


def serialize_json(obj):
    if isinstance(obj, datetime.datetime):
        if obj.utcoffset() is not None:
            obj = obj - obj.utcoffset()
        millis = int(calendar.timegm(obj.timetuple()) * 1000 + obj.microsecond / 1000)
        return millis
    return str(obj)
