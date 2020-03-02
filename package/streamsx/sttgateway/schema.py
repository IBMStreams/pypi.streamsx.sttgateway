# coding=utf-8
# Licensed Materials - Property of IBM
# Copyright IBM Corp. 2020


from streamsx.topology.schema import StreamSchema
#
# Defines Message types with default attribute names and types.
_SPL_SCHEMA_ACCESS_TOKEN = 'tuple<rstring access_token, rstring refresh_token, rstring scope, int64 expiration, rstring token_type, int64 expires_in>'

class GatewaySchema:
    """
    Structured stream schema
    
    """

    AccessToken = StreamSchema (_SPL_SCHEMA_ACCESS_TOKEN)
    """
    This schema can be used as output for ...
    
    The schema defines following attributes

    """
    pass

