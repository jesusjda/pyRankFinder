class Option:
    _value = None
    _desc = ""
    
    def __init__(self, value, description):
        self._value = value
        self._desc = description

    def set_value(self, value):
        self._value = value

    def get_value(self):
        return self._value

    def __repr__(self):
        return self._value + " " + self._desc
    
class Configuration(dict):

    _ops = {}
    _defaults = {}
    
    def __init__(self, defaults={}):
        self._defaults = defaults
        self._ops = defaults.copy()

    def __setitem__(self, key, item):
        self._ops[key] = item

    def __getitem__(self, key):
        if key in _ops:
            return self._ops[key]
        return None

    def __repr__(self):
        return "Configuration Class: "+repr(self._ops)

    def __len__(self):
        return len(self._ops)

    def __delitem__(self, key):
        del self._ops[key]

    def clear(self):
        ret = self._ops.clear()
        self._loadDefaults()
        return ret

    def has_key(self, key):
        return self._ops.has_key(key)

    def copy(self):
        return Configuration(self._ops.copy())

    def keys(self):
        return self._ops.keys()

    def values(self):
        return self._ops.values()

    def items(self):
        return self._ops.items()

    def __cmp__(self, config):
        return cmp(self._ops, config._ops)

    def __contains__(self, item):
        return item in self._ops

    def __iter__(self):
        return iter(self._ops)

    def __unicode__(self):
        return unicode(repr(self._ops))
    
    def set_prop(self, name, value):
        self._ops[name] = value

    def get_original_values(self):
        return self._defaults

    def _loadDefaults(self):
        self._ops = {
            "verbosity" : 0
        }
        for k, v in self._defaults:
            self._ops[k] = v
        
class ConfigBuilder:

    _params = {}
    def __init__(self):
        self._params = {
            
            
        }
