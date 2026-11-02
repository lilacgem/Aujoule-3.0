"""Explicit experimental adaptation of the received evoMetrics formula, not new core logic."""
import math

SCHEMA = 'AUEVO-EvoMetricsExperiment/v0.1'


def validate_config(config):
    required = {'schema', 'enabled', 'configuredFocus', 'sessionCount', 'priorLeftover', 'bandRmsReference', 'evaluationMode'}
    if not isinstance(config, dict) or set(config) != required or config['schema'] != SCHEMA:
        raise ValueError('Invalid or unsupported evoMetrics experiment configuration.')
    if type(config['enabled']) is not bool: raise ValueError('enabled must be explicitly true or false.')
    for name, minimum, maximum in [('configuredFocus',0,1), ('bandRmsReference',.000001,1)]:
        value=config[name]
        if type(value) not in (int,float) or not math.isfinite(value) or not minimum<=value<=maximum:
            raise ValueError(f'Invalid configured {name}.')
    for name, maximum in [('sessionCount',1000000), ('priorLeftover',9)]:
        if type(config[name]) is not int or not 0<=config[name]<=maximum: raise ValueError(f'Invalid {name}.')
    if config['evaluationMode']!='independent-windows-fixed-context':
        raise ValueError('Only independent-window evaluation is supported; no history is advanced.')
    return config


def digital_root(number):
    value=math.floor(abs(number)+.5)
    return 0 if value==0 else (value-1)%9+1


def evaluate(band_power, config):
    validate_config(config)
    if not config['enabled']: return None
    if set(band_power)!={'bass','mid','high'} or any(not math.isfinite(value) or value<0 for value in band_power.values()):
        raise ValueError('Three finite, nonnegative common-band powers are required.')
    normalized={key:min(1., math.sqrt(value)/config['bandRmsReference']) for key,value in band_power.items()}
    voice_energy=sum(normalized.values())/3
    focus=config['configuredFocus']
    new_variable=min(1.,config['sessionCount']*.01)
    delta=voice_energy*focus+new_variable*369
    session_number=max(1,math.floor(abs(delta)*100+.5))
    level=config['priorLeftover']+digital_root(session_number)
    leftover_raw=session_number//10
    leftover=leftover_raw if leftover_raw<=9 else digital_root(leftover_raw)
    root=digital_root(level)
    gate=root in (3,6,9)
    constraints=[1,2,4,5,7,8]
    shape={'p':1,'q':1} if gate else {'p':root,'q':constraints[(constraints.index(root)+2)%len(constraints)]}
    return {'evidenceClass':'DERIVED_EXPERIMENTAL','normalizedBandRms':normalized,
            'normalizationClippedBands':[key for key,value in band_power.items() if math.sqrt(value)>config['bandRmsReference']],
            'voiceEnergy':voice_energy,'configuredFocus':focus,'focusOrigin':'CONFIGURED_NOT_CAMERA_MEASURED',
            'newVariable':new_variable,'audioContribution':voice_energy*focus,'sessionCountContribution':new_variable*369,
            'evolutionDelta':delta,'sessionNumber':session_number,'gRootLevel':level,'digitalRoot':root,
            'nextLeftover':leftover,'isGate':gate,'shape':shape,
            'historyAdvanced':False,'symbolicConstant':{'value':369,'origin':'AUEVO_DEFINED'}}
