from django.conf import settings
from mediagenerator.generators.bundles.base import SubProcessFilter

COMPILATION_LEVEL = getattr(settings, 'CLOSURE_COMPILATION_LEVEL',
                            'SIMPLE_OPTIMIZATIONS')

class Closure(SubProcessFilter):
    def __init__(self, **kwargs):
        self.config(kwargs, compilation_level=COMPILATION_LEVEL)
        super().__init__(**kwargs)
        assert self.filetype == 'js', (
            f'Closure only supports compilation to js. '
            f'The parent filter expects "{self.filetype}".')

    def get_output(self, variation):
        # We import this here, so App Engine Helper users don't get import
        # errors.
        compressor = settings.CLOSURE_COMPILER_PATH

        for input in self.get_input(variation):
            try:
                yield self.run_process([
                    'java', '-jar', compressor, '--charset', 'utf-8', '--compilation_level', self.compilation_level,
                ], input=input)
            except Exception as e:
                raise ValueError(
                    "Failed to execute Java VM or Closure. "
                    "Please make sure that you have installed Java "
                    "and that it's in your PATH and that you've configured "
                    "CLOSURE_COMPILER_PATH in your settings correctly.\n"
                    "Error was: {}".format(e)
                )
