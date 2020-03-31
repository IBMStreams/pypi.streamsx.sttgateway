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
import streamsx.spl.toolkit

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

def configure_connection(instance, credentials, name='sttConnection'):
    """Configures IBM Streams for a connection to Watson STT.

    Creates an application configuration object containing the required properties with connection information.

    Example for creating a configuration for a Streams instance with connection details::

        from streamsx.rest import Instance
        import streamsx.topology.context
        from icpd_core import icpd_util
        import streamsx.sttgateway as stt
        
        cfg=icpd_util.get_service_instance_details(name='your-streams-instance')
        cfg[streamsx.topology.context.ConfigParams.SSL_VERIFY] = False
        instance = Instance.of_service(cfg)
        sample_credentials = {
            'url': 'wss://hostplaceholder/speech-to-text/ibm-wc/instances/1188888444444/api/v1/recognize',
            'access_token': 'sample-access-token'
        }
        app_cfg = stt.configure_connection(instance, credentials=sample_credentials, name='stt-sample')

    Args:
        instance(streamsx.rest_primitives.Instance): IBM Streams instance object.
        credentials(dict): dict containing "url" and "access_token" (STT service in Cloud Pak for Data) or "url" and "api_key" and "iam_token_url" (STT IBM cloud service).
        name(str): Name of the application configuration

    Returns:
        Name of the application configuration.
    """

    # Prepare operator (toolkit) specific properties for application configuration
    description = 'Config for STT connection ' + name
    properties = {}
    url, access_token, api_key, iam_token_url = _read_credentials(credentials)
    if url is not None:
        properties['url']=url
    if access_token is not None:
        properties['accessToken']=access_token
    if api_key is not None:
        properties['apiKey']=api_key
    if iam_token_url is not None:
        properties['iamTokenURL']=iam_token_url
    
    # check if application configuration exists
    app_config = instance.get_application_configurations(name=name)
    if app_config:
        print ('update application configuration: '+name)
        app_config[0].update(properties)
    else:
        print ('create application configuration: '+name)
        instance.create_application_configuration(name, properties, description)
    return name


class WatsonSTT(streamsx.topology.composite.Map):
    """
    Composite map transformation for WatsonSTT

    Example for reading audio files and speech to text transformation::

        import streamsx.sttgateway as stt
        import streamsx.standard.files as stdfiles
        from streamsx.topology.topology import Topology
        from streamsx.topology.schema import StreamSchema
        import streamsx.spl.op as op
        import typing
        import os
        
        # credentials for WatsonSTT service 
        stt_creds = {
            "url": "wss://xxxx/instances/xxxx/v1/recognize",
            "access_token": "xxxx",
        }
        
        topo = Topology()
    
        # add sample files to application bundle
        sample_audio_dir='/your-directory-with-wav-files' # either dir or single file
        dirname = 'etc'
        topo.add_file_dependency(sample_audio_dir, dirname) 
        if os.path.isdir(sample_audio_dir):
            dirname = dirname + '/' + os.path.basename(sample_audio_dir) 
        dirname = op.Expression.expression('getApplicationDir()+"/'+dirname+'"')

        s = topo.source(stdfiles.DirectoryScan(directory=dirname, pattern='.*call-center.*\.wav$'))
        files = s.map(stdfiles.BlockFilesReader(block_size=512, file_name='conversationId'), schema=StreamSchema('tuple<blob speech, rstring conversationId>'))

        SttResult = typing.NamedTuple('SttResult', [('conversationId', str), ('utteranceText', str)])
        res = files.map(stt.WatsonSTT(credentials=stt_creds, base_language_model='en-US_NarrowbandModel'), schema=SttResult)

        res.print()

    Attributes
    ----------
    credentials : str|dict
        Name of the application configuration or dict containing the credentials for WatsonSTT. The dict contains either "url" and "access_token" (STT service in Cloud Pak for Data) or "url" and "api_key" and "iam_token_url" (STT IBM cloud service)
    base_language_model : str
        This parameter specifies the name of the Watson STT base language model that should be used, see: https://cloud.ibm.com/docs/services/speech-to-text?topic=speech-to-text-input#models
    partial_result : bool
        ``True`` to get partial utterances, ``False`` to get the full text after transcribing the entire audio (default).
    options : kwargs
        The additional optional parameters as variable keyword arguments.
    """

    def __init__(self, credentials, base_language_model, partial_result=False, **options):

        self.credentials = credentials
        self.base_language_model = base_language_model
        self.partial_result = partial_result

        self.content_type = None
        if 'content_type' in options:
            self.content_type = options.get('content_type')

    @property
    def content_type(self):
        """
            str: Content type to be used for transcription. (Default is audio/wav) 
        """
        return self._content_type

    @content_type.setter
    def content_type(self, value):
        self._content_type = value


    def populate(self, topology, stream, schema, name, **options):
        _add_toolkit_dependency(topology)

        is_stt_result_schema = False
        if schema is None:
            is_stt_result_schema = True
            schema = GatewaySchema.STTResult
            if self.partial_result:
                schema = schema.extend(GatewaySchema.STTResultPartialExtension)

        if schema is GatewaySchema.STTResult:
            is_stt_result_schema = True

        if isinstance(self.credentials, dict):
            url, access_token, api_key, iam_token_url = _read_credentials(self.credentials)
            app_config_name = None
        else:
            url=None
            access_token=None
            api_key=None
            iam_token_url = None
            app_config_name = self.credentials

        _op_token = _IAMAccessTokenGenerator(topology=topology, schema=GatewaySchema.AccessToken, appConfigName=app_config_name, accessToken=access_token, apiKey=api_key, iamTokenURL=iam_token_url, name=name)
        token_stream = _op_token.outputs[0]

        _op = _WatsonSTT(stream, token_stream, schema=schema, baseLanguageModel=self.base_language_model, contentType=self.content_type, name=name)
        
        if self.partial_result:
            _op.params['sttResultMode'] = _op.expression('partial')
        else:
            _op.params['sttResultMode'] = _op.expression('complete');
        if app_config_name is not None:
            _op.params['uri'] = _op.expression('getApplicationConfigurationProperty(\"'+app_config_name+'\", \"url\", \"\")')
        else:
            _op.params['uri'] = url

        if is_stt_result_schema:
            if self.partial_result:
                _op.finalizedUtterance = _op.output(_op.outputs[0], _op.expression('isFinalizedUtterance()'))
                _op.confidence = _op.output(_op.outputs[0], _op.expression('getConfidence()'))
            _op.transcriptionCompleted = _op.output(_op.outputs[0], _op.expression('isTranscriptionCompleted()'))
            _op.sttErrorMessage = _op.output(_op.outputs[0], _op.expression('getSTTErrorMessage()'))
            _op.utteranceStartTime = _op.output(_op.outputs[0], _op.expression('getUtteranceStartTime()'))
            _op.utteranceEndTime = _op.output(_op.outputs[0], _op.expression('getUtteranceEndTime()'))
            _op.utterance = _op.output(_op.outputs[0], _op.expression('getUtteranceText()'))

        return _op.outputs[0]




class _WatsonSTT(streamsx.spl.op.Invoke):
    def __init__(self, stream, token_stream, schema=None, baseLanguageModel=None, uri=None, acousticCustomizationId=None, baseModelVersion=None, contentType=None, cpuYieldTimeInAudioSenderThread=None, customizationId=None, customizationWeight=None, filterProfanity=None, keywordsSpottingThreshold=None, keywordsToBeSpotted=None, maxConnectionRetryDelay=None, maxUtteranceAlternatives=None, nonFinalUtterancesNeeded=None, smartFormattingNeeded=None, sttLiveMetricsUpdateNeeded=None, sttRequestLogging=None, sttResultMode=None, websocketLoggingNeeded=None, wordAlternativesThreshold=None, name=None):
        topology = stream.topology
        kind="com.ibm.streamsx.sttgateway.watson::WatsonSTT"
        inputs=[stream,token_stream]
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


class _IAMAccessTokenGenerator(streamsx.spl.op.Source):
    def __init__(self, topology, schema, appConfigName=None, accessToken=None, apiKey=None, iamTokenURL=None, defaultExpiresIn=None, guardTime=None, maxRetryDelay=None, failureRetryDelay=None, initDelay=None, expiresInTestValue=None, name=None):
        kind="com.ibm.streamsx.sttgateway.watson::IAMAccessTokenGenerator"
        inputs=None
        schemas=schema
        params = dict()
        if appConfigName is not None:
            params['appConfigName'] = appConfigName
        if accessToken is not None:
            params['accessToken'] = accessToken
        if apiKey is not None:
            params['apiKey'] = apiKey
        if iamTokenURL is not None:
            params['iamTokenURL'] = iamTokenURL
        if defaultExpiresIn is not None:
            params['defaultExpiresIn'] = defaultExpiresIn
        if guardTime is not None:
            params['guardTime'] = guardTime
        if maxRetryDelay is not None:
            params['maxRetryDelay'] = maxRetryDelay
        if failureRetryDelay is not None:
            params['failureRetryDelay'] = failureRetryDelay
        if initDelay is not None:
            params['initDelay'] = initDelay
        if expiresInTestValue is not None:
            params['expiresInTestValue'] = expiresInTestValue

        super(_IAMAccessTokenGenerator, self).__init__(topology,kind,schemas,params,name)

