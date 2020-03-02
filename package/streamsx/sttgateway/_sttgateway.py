# coding=utf-8
# Licensed Materials - Property of IBM
# Copyright IBM Corp. 2020

import os
import streamsx.spl.op as op
import streamsx.spl.types
from streamsx.topology.schema import CommonSchema, StreamSchema
from streamsx.spl.types import rstring
import datetime
import json
from streamsx.sttgateway.schema import GatewaySchema
import streamsx.topology.composite

def _add_toolkit_dependency(topo):
    # IMPORTANT: Dependency of this python wrapper to a specific toolkit version
    # This is important when toolkit is not set with streamsx.spl.toolkit.add_toolkit (selecting toolkit from remote build service)
    streamsx.spl.toolkit.add_toolkit_dependency(topo, 'com.ibm.streamsx.sttgateway', '[2.0.0,3.0.0)')

def _read_credentials(credentials):
    url = None
    access_token = None
    api_key = None
    iam_token_url = None
    if isinstance(credentials, dict):
        url = credentials.get('url')
        access_token = credentials.get('access_token')
        api_key = credentials.get('api_key')
        iam_token_url = credentials.get('iam_token_url')
    else:
        raise TypeError(credentials)
    return url, access_token, api_key, iam_token_url

class WatsonSTT(streamsx.topology.composite.Map):
    """
    Composite map transformation for WatsonSTT

    """

    def __init__(self, credentials, base_language_model):

        self.credentials = credentials
        self.base_language_model = base_language_model

        

    def populate(self, topology, stream, schema, name, **options):

        app_config_name = self.credentials
        if isinstance(self.credentials, dict):
            url, access_token, api_key, iam_token_url = _read_credentials(credentials)
            app_config_name = None
        else:
            url=None
            access_token=None
            api_key=None
            iam_token_url = None
            app_config_name = self.credentials


        _op = _WatsonSTT(stream=stream, schema=schema, name=name)
        
        _op.params['baseLanguageModel'] = self.base_language_model
        if app_config_name is not None:
            _op.params['uri'] = _op.expression('getApplicationConfigurationProperty('+app_config_name+', \"url\", \"\")')
        else:
            _op.params['uri'] = url

        return _op.outputs[0]




class _WatsonSTT(streamsx.spl.op.Invoke):
    def __init__(self, stream, schema=None, baseLanguageModel=None, uri=None, acousticCustomizationId=None, baseModelVersion=None, contentType=None, cpuYieldTimeInAudioSenderThread=None, customizationId=None, customizationWeight=None, filterProfanity=None, keywordsSpottingThreshold=None, keywordsToBeSpotted=None, maxConnectionRetryDelay=None, maxUtteranceAlternatives=None, nonFinalUtterancesNeeded=None, smartFormattingNeeded=None, sttLiveMetricsUpdateNeeded=None, sttRequestLogging=None, sttResultMode=None, websocketLoggingNeeded=None, wordAlternativesThreshold=None, name=None):
        topology = stream.topology
        kind="com.ibm.streamsx.sttgateway::WatsonSTT"
        inputs=stream
        schemas=schema
        params = dict()
        if baseLanguageModel is not None:
            params['baseLanguageModel'] = baseLanguageModel
        if uri is not None:
            params['uri'] = uri
        if acousticCustomizationId is not None:
            params['acousticCustomizationId'] = acousticCustomizationId
        if baseModelVersion is not None:
            params['baseModelVersion'] = baseModelVersion
        if contentType is not None:
            params['contentType'] = contentType
        if cpuYieldTimeInAudioSenderThread is not None:
            params['cpuYieldTimeInAudioSenderThread'] = cpuYieldTimeInAudioSenderThread
        if customizationId is not None:
            params['customizationId'] = customizationId
        if customizationWeight is not None:
            params['customizationWeight'] = customizationWeight
        if filterProfanity is not None:
            params['filterProfanity'] = filterProfanity
        if keywordsSpottingThreshold is not None:
            params['keywordsSpottingThreshold'] = keywordsSpottingThreshold
        if keywordsToBeSpotted is not None:
            params['keywordsToBeSpotted'] = keywordsToBeSpotted
        if maxConnectionRetryDelay is not None:
            params['maxConnectionRetryDelay'] = maxConnectionRetryDelay
        if maxUtteranceAlternatives is not None:
            params['maxUtteranceAlternatives'] = maxUtteranceAlternatives
        if nonFinalUtterancesNeeded is not None:
            params['nonFinalUtterancesNeeded'] = nonFinalUtterancesNeeded
        if smartFormattingNeeded is not None:
            params['smartFormattingNeeded'] = smartFormattingNeeded
        if sttLiveMetricsUpdateNeeded is not None:
            params['sttLiveMetricsUpdateNeeded'] = sttLiveMetricsUpdateNeeded
        if sttRequestLogging is not None:
            params['sttRequestLogging'] = sttRequestLogging
        if sttResultMode is not None:
            params['sttResultMode'] = sttResultMode
        if websocketLoggingNeeded is not None:
            params['websocketLoggingNeeded'] = websocketLoggingNeeded
        if wordAlternativesThreshold is not None:
            params['wordAlternativesThreshold'] = wordAlternativesThreshold

        super(_WatsonSTT, self).__init__(topology,kind,inputs,schema,params,name)

