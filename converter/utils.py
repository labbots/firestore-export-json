import base64
import calendar
import datetime

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


def embedded_entity_to_dict(embedded_entity, data):
    ep = entity_pb2.EntityProto()
    ep.ParseFromString(embedded_entity)
    d = MessageToDict(ep)
    for entry in d['rawProperty']:
        if 'meaning' in entry and entry['meaning'] == "ENTITY_PROTO":
            dt = {}
            data[entry['name']] = embedded_entity_to_dict(base64.b64decode(entry['value']['stringValue']), dt)
        else:
            if entry['value']:
                data[entry['name']] = base64.b64decode(entry['value']['stringValue']).decode('utf-8')
            else:
                data[entry['name']] = None
    return data


def serialize_json(obj):
    if isinstance(obj, datetime.datetime):
        if obj.utcoffset() is not None:
            obj = obj - obj.utcoffset()
        millis = int(
            calendar.timegm(obj.timetuple()) * 1000 +
            obj.microsecond / 1000
        )
        return millis
    # raise TypeError('Not sure how to serialize %s' % (obj,))
    return str(obj)
