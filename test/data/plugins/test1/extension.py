def preprocess_commands(ctx):
    return (('ls', '-l'),)

def service_command(ctx):
    return ('sleep', '1')

def service_environment(ctx):
    return {'TEST_ENV': '1234'}

def compile(installer):
    print 'Hello World!'
    return 0
