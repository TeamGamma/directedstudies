

class CommandError(Exception):
    pass


class UnknownCommandError(CommandError):
    pass


class InvalidCommandArgumentsError(CommandError):
    pass


class CommandHandler(object):
    # Associates command labels (e.g. BUY) to subclasses of CommandHandler
    commands = {}

    @classmethod
    def get_handler(cls, label):
        """ Finds the CommandHandler associated with label """
        if label not in cls.commands:
            raise UnknownCommandError(label)

        return cls.commands[label]()

    @classmethod
    def register_command(cls, label, command):
        """
        Registers command with CommandHandler so it can be looked up by label
        """
        cls.commands[label] = command


class EchoCommand(CommandHandler):
    """ Echoes a single argument back to the client """
    def run(self, message):
        return message + '\n'

CommandHandler.register_command('ECHO', EchoCommand)


class UppercaseCommand(CommandHandler):
    """ Like ECHO, but returns the message in uppercase """
    def run(self, message):
        return message.upper() + '\n'

CommandHandler.register_command('UPPER', UppercaseCommand)


