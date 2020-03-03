# coding=utf-8
# Licensed Materials - Property of IBM
# Copyright IBM Corp. 2020


from streamsx.topology.schema import StreamSchema
#
# Defines Message types with default attribute names and types.
_SPL_SCHEMA_ACCESS_TOKEN = 'tuple<rstring access_token, rstring refresh_token, rstring scope, int64 expiration, rstring token_type, int64 expires_in>'

_SPL_SCHEMA_STT_RESULT = 'tuple<rstring conversationId,	boolean finalizedUtterance, boolean transcriptionCompleted, rstring sttErrorMessage, float64 utteranceStartTime, float64 utteranceEndTime, float64 confidence, rstring utterance>'

_SPL_SCHEMA_STT_INPUT = 'tuple<rstring conversationId, blob speech>'
			

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

    STTResult = StreamSchema (_SPL_SCHEMA_STT_RESULT)
    """
    This schema can be used as output for ...
    
    The schema defines following attributes

    """
    pass

    STTInput = StreamSchema (_SPL_SCHEMA_STT_INPUT)
    """
    This schema can be used as output for ...
    
    The schema defines following attributes

    """
    pass

