# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: transactions.proto
# Protobuf Python Version: 4.25.3
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x12transactions.proto\x12\x0ctransactions\"O\n\x0bTransaction\x12\x0e\n\x06nodeID\x18\x01 \x01(\x05\x12\x0f\n\x07\x62lkAddr\x18\x02 \x01(\x05\x12\x11\n\tdirection\x18\x03 \x01(\x05\x12\x0c\n\x04tick\x18\x04 \x01(\x05\"C\n\x10Transaction_list\x12/\n\x0ctransactions\x18\x01 \x03(\x0b\x32\x19.transactions.Transaction')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'transactions_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_TRANSACTION']._serialized_start=36
  _globals['_TRANSACTION']._serialized_end=115
  _globals['_TRANSACTION_LIST']._serialized_start=117
  _globals['_TRANSACTION_LIST']._serialized_end=184
# @@protoc_insertion_point(module_scope)
