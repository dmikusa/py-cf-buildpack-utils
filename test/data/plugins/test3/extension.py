def preprocess_commands(ctx):
    return (('echo', '"Test3"'),)

def service_commands(ctx):
    return {'server': ('sleep', '3')}

def service_environment(ctx):
    return {'TEST_ENV': '9876'}

def compile(installer):
    raise ValueError("Intentional")
    return 0
