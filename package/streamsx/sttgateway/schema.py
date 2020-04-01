# coding=utf-8
# Licensed Materials - Property of IBM
# Copyright IBM Corp. 2020


from streamsx.topology.schema import StreamSchema
#
# Defines Message types with default attribute names and types.
_SPL_SCHEMA_ACCESS_TOKEN = 'tuple<rstring access_token, rstring refresh_token, rstring scope, int64 expiration, rstring token_type, int64 expires_in>'

_SPL_SCHEMA_STT_RESULT = 'tuple<rstring conversationId,	boolean transcriptionCompleted, rstring sttErrorMessage, float64 utteranceStartTime, float64 utteranceEndTime, rstring utterance>'

_SPL_SCHEMA_STT_RESULT_PARTIAL = 'tuple<boolean finalizedUtterance, float64 confidence>'

_SPL_SCHEMA_STT_INPUT = 'tuple<rstring conversationId, blob speech>'

_SPL_SCHEMA_STT_RESULT_KEYWORD_SPOTTING = 'tuple<map<rstring, list<tuple<float64 startTime, float64 endTime, float64 confidence>>> keywordsSpottingResults>'
			

class GatewaySchema:
    """
    Structured stream schemas for :py:meth:`~streamsx.sttgateway.WatsonSTT`
    
    """

    STTResult = StreamSchema (_SPL_SCHEMA_STT_RESULT)
    """
    This schema is used as output in :py:meth:`~streamsx.sttgateway.WatsonSTT`
    
    The schema defines following attributes

    * conversationId(rstring) - identifier, for example file name
    * transcriptionCompleted(boolean) - boolean value to indicate whether the full transcription/conversation is completed
    * sttErrorMessage(rstring) - Watson STT error message if any.
    * utteranceStartTime(float64) - start time of an utterance relative to the start of the audio
    * utteranceEndTime(float64) - end time of an utterance relative to the start of the audio
    * utterance(rstring) - the transcription of audio in the form of a single utterance

    """
    pass

    STTResultPartialExtension = StreamSchema (_SPL_SCHEMA_STT_RESULT_PARTIAL)
    """
    This schema is added to STTResult schema when result mode is partial in :py:meth:`~streamsx.sttgateway.WatsonSTT`
    
    The schema defines following attributes

    * finalizedUtterance(boolean) - boolean value to indicate if this is an interim partial utterance or a finalized utterance. 
    * confidence(float64) - confidence value for an interim partial utterance or for a finalized utterance or for the full text.

    """
    pass


    STTResultKeywordExtension = StreamSchema (_SPL_SCHEMA_STT_RESULT_KEYWORD_SPOTTING)
    """
    This schema is added to STTResult schema when keywords_to_be_spotted is set in :py:meth:`~streamsx.sttgateway.WatsonSTT`
    
    The schema defines following attributes

    * keywordsSpottingResults(map<rstring, list<tuple<float64 startTime, float64 endTime, float64 confidence>>>) - The keys of the map are the spotted keywords. 

    """
    pass


    STTInput = StreamSchema (_SPL_SCHEMA_STT_INPUT)
    """
    Use this schema as input for :py:meth:`~streamsx.sttgateway.WatsonSTT`
    
    The schema defines following attributes

    * conversationId(rstring) - identifier, for example file name
    * speech(blob) - audio data

    """
    pass


    AccessToken = StreamSchema (_SPL_SCHEMA_ACCESS_TOKEN)
    """
    This schema is used internally in :py:meth:`~streamsx.sttgateway.WatsonSTT` by the access token generator.
    """
    pass

