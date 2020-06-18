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
import streamsx.toolkits


_TOOLKIT_NAME = 'com.ibm.streamsx.sttgateway'

def _add_toolkit_dependency(topo):
    # IMPORTANT: Dependency of this python wrapper to a specific toolkit version
    # This is important when toolkit is not set with streamsx.spl.toolkit.add_toolkit (selecting toolkit from remote build service)
    streamsx.spl.toolkit.add_toolkit_dependency(topo, _TOOLKIT_NAME, '[2.0.0,3.0.0)')

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

def download_toolkit(url=None, target_dir=None):
    r"""Downloads the latest sttgateway toolkit from GitHub.

    Example for updating the sttgateway toolkit for your topology with the latest toolkit from GitHub::

        import streamsx.sttgateway as stt
        from streamsx.spl import toolkit
        # download sttgateway toolkit from GitHub
        stt_toolkit_location = stt.download_toolkit()
        # add the toolkit to topology
        toolkit.add_toolkit(topology, stt_toolkit_location)

    Example for updating the topology with a specific version of the sttgateway toolkit using a URL::

        import streamsx.sttgateway as stt
        from streamsx.spl import toolkit
        url220 = 'https://github.com//IBMStreams/streamsx.sttgateway/releases/download/v2.2.0/streamsx.sttgateway-2.2.0-ced653b-20200331-1219.tgz'
        stt_toolkit_location = stt.download_toolkit(url=url220)
        toolkit.add_toolkit(topology, stt_toolkit_location)

    Args:
        url(str): Link to toolkit archive (\*.tgz) to be downloaded. Use this parameter to 
            download a specific version of the toolkit.
        target_dir(str): the directory where the toolkit is unpacked to. If a relative path is given,
            the path is appended to the system temporary directory, for example to /tmp on Unix/Linux systems.
            If target_dir is ``None`` a location relative to the system temporary directory is chosen.

    Returns:
        str: the location of the downloaded sttgateway toolkit

    .. note:: This function requires an outgoing Internet connection
    .. versionadded:: 0.5
    """
    _toolkit_location = streamsx.toolkits.download_toolkit (toolkit_name=_TOOLKIT_NAME, url=url, target_dir=target_dir)
    return _toolkit_location

def configure_connection(instance, credentials, name='sttConnection'):
    """Configures IBM Streams for a connection to Watson STT.

    Creates an application configuration object containing the required properties with connection information.

    Example for creating a configuration for a Streams instance with connection details::

        from icpd_core import icpd_util
        from streamsx.rest_primitives import Instance
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

    This operator is designed to ingest audio data in the form of a file (.wav, .mp3 etc.) or RAW audio and then transcribe that audio into text via the IBM Watson STT (Speech To Text) cloud service. It does that by sending the audio data to the configured Watson STT service running in the IBM public cloud or in the IBM Cloud Pak for Data via the Websocket interface. It then outputs transcriptions of speech in the form of utterances or in full text as configured. An utterance is a group of transcribed words meant to approximate a sentence. Audio data must be in 16-bit little endian, mono format. For the Telephony model and configurations, the audio must have an 8 kHz sampling rate. For the Broadband model and configurations, the audio must have a 16 kHz sampling rate. The data can be provided as a .wav file or as RAW uncompressed PCM audio.

    .. note:: 
        The input stream **must** contain an attribute with the name ``speech`` of type ``blob`` or ``bytes``, for example 

        * ``StreamSchema('tuple<blob speech>')``
        * ``typing.NamedTuple('SttInput', [('speech', bytes)])``.

    A window punctuation marker or an empty speech blob may be used to mark the end of an conversation. Thus a conversation can be a composite of multiple audio files. When the end of conversation is encountered, the STT engine delivers all results of the current conversation and flushes all buffers.

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
        SttInput = typing.NamedTuple('SttInput', [('conversationId', str), ('speech', bytes)])
        files = s.map(stdfiles.BlockFilesReader(block_size=512, file_name='conversationId'), schema=SttInput)

        SttResult = typing.NamedTuple('SttResult', [('conversationId', str), ('utteranceText', str)])
        res = files.map(stt.WatsonSTT(credentials=stt_creds, base_language_model='en-US_NarrowbandModel'), schema=SttResult)

        res.print()

    Attributes
    ----------
    credentials : str|dict
        Name of the application configuration or dict containing the credentials for WatsonSTT. The dict contains either "url" and "access_token" (STT service in Cloud Pak for Data) or "url" and "api_key" and "iam_token_url" (STT IBM cloud service)

        Example for WatsonSTT in Cloud Pak for Data::

            credentials = {
                "url": "wss://xxxx/instances/xxxx/v1/recognize",
                "access_token": "xxxx",
            }

        Example for WatsonSTT IBM cloud service::

            credentials = {
                "url": "wss://xxxx/instances/xxxx/v1/recognize",
                "api_key": "xxxx",
                "iam_token_url": "https://iam.cloud.ibm.com/identity/token",
            }

    base_language_model : str
        This parameter specifies the name of the Watson STT base language model that should be used. https://cloud.ibm.com/docs/services/speech-to-text?topic=speech-to-text-input#models
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
        self.filter_profanity = None
        self.keywords_spotting_threshold = None
        self.keywords_to_be_spotted = None
        self.max_utterance_alternatives = None
        if 'content_type' in options:
            self.content_type = options.get('content_type')
        if 'filter_profanity' in options:
            self.filter_profanity = options.get('filter_profanity')
        if 'keywords_spotting_threshold' in options:
            self.keywords_spotting_threshold = options.get('keywords_spotting_threshold')
        if 'keywords_to_be_spotted' in options:
            self.keywords_to_be_spotted = options.get('keywords_to_be_spotted')
        if 'max_utterance_alternatives' in options:
            self.max_utterance_alternatives = options.get('max_utterance_alternatives')

    @property
    def content_type(self):
        """
            str: Content type to be used for transcription. (Default is audio/wav) 
        """
        return self._content_type

    @content_type.setter
    def content_type(self, value):
        self._content_type = value

    @property
    def filter_profanity(self):
        """
            bool: This parameter indicates whether profanity should be filtered from a transcript. (Default is false)
            https://cloud.ibm.com/docs/services/speech-to-text?topic=speech-to-text-output#profanity_filter 
        """
        return self._filter_profanity

    @filter_profanity.setter
    def filter_profanity(self, value):
        self._filter_profanity = value

    @property
    def keywords_spotting_threshold(self):
        """
            float: This parameter specifies the minimum confidence level that the STT service must have for an utterance word to match a given keyword. A value of 0.0 disables this feature. Valid value must be less than 1.0. (Default is 0.3)
            https://cloud.ibm.com/docs/services/speech-to-text?topic=speech-to-text-output#keyword_spotting 
        """
        return self._keywords_spotting_threshold

    @keywords_spotting_threshold.setter
    def keywords_spotting_threshold(self, value):
        self._keywords_spotting_threshold = value

    @property
    def keywords_to_be_spotted(self):
        """
            list(str): This parameter specifies a list (array) of strings to be spotted. (Default is an empty list)
        Example for list format::

        ['keyword1','keyword2']

        Example for str format::

        "['keyword1','keyword2']"
        """
        return self._keywords_to_be_spotted

    @keywords_to_be_spotted.setter
    def keywords_to_be_spotted(self, value):
        self._keywords_to_be_spotted = value

    @property
    def max_utterance_alternatives(self):
        """
            int: This parameter indicates the required number of n-best alternative hypotheses for the transcription results. (Default is 3)
            https://cloud.ibm.com/docs/services/speech-to-text?topic=speech-to-text-output#max_alternatives

            .. note:: This parameter is ignored if ``partial_result`` is ``False``.

        """
        return self._max_utterance_alternatives

    @max_utterance_alternatives.setter
    def max_utterance_alternatives(self, value):
        self._max_utterance_alternatives = value

    @property
    def non_final_utterances_needed(self):
        """
            bool: This parameter controls the output of non final utterances. (Default is False)

            .. note:: This parameter is ignored if ``partial_result`` is ``False``.

        """
        return self._non_final_utterances_needed

    @non_final_utterances_needed.setter
    def non_final_utterances_needed(self, value):
        self._non_final_utterances_needed = value


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

        if self.keywords_to_be_spotted is not None and is_stt_result_schema:
            schema = schema.extend(GatewaySchema.STTResultKeywordExtension)

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
        
        if self.filter_profanity is not None:
            if self.filter_profanity:
                _op.params['filterProfanity'] = _op.expression('true')
        if self.keywords_spotting_threshold is not None:
            _op.params['keywordsSpottingThreshold'] = streamsx.spl.types.float64(self.keywords_spotting_threshold)
        if self.keywords_to_be_spotted is not None:
            if is_stt_result_schema:
                _op.keywordsSpottingResults = _op.output(_op.outputs[0], _op.expression('getKeywordsSpottingResults()'))
            if isinstance(self.keywords_to_be_spotted, str):
                _op.params['keywordsToBeSpotted'] = _op.expression(self.keywords_to_be_spotted)
            elif isinstance(self.keywords_to_be_spotted, list):
                i = 0
                keywords = ''
                for word in self.keywords_to_be_spotted: 
                    if i > 0:
                        keywords = keywords + ','
                    keywords = keywords + '\"'+word+'\"'
                    i = i + 1
                _op.params['keywordsToBeSpotted'] = _op.expression('['+keywords+']') # list of string

        if self.partial_result:
            _op.params['sttResultMode'] = _op.expression('partial')
            if self.max_utterance_alternatives is not None:
                _op.params['maxUtteranceAlternatives'] = streamsx.spl.types.int32(self.max_utterance_alternatives)
            if self.non_final_utterances_needed is not None:
                if self.non_final_utterances_needed:
                    _op.params['nonFinalUtterancesNeeded'] = _op.expression('true')

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

