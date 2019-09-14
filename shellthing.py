#!/usr/bin/env python3

"""
A simple shell users can use to sift through data and optionally operate on that data.
"""

from itertools import chain
import json
import readline
import sys

if 'libedit' in readline.__doc__:
    readline.parse_and_bind("bind ^I rl_complete")
else:
    readline.parse_and_bind("tab: complete")

BASE_PROMPT = 'shellthing'

class MyCompleter():
    """A tab-complete class for command line fun."""

    def __init__(self, options):
        self.options = sorted(options)

    def complete(self, text, state):
        if state == 0:  # on first trigger, build possible matches
            if text:  # cache matches (entries that start with entered text)
                self.matches = [s for s in self.options
                                if s and s.startswith(text)]
            else:  # no text entered, all matches possible
                self.matches = self.options[:]

        # return match indexed by state
        try:
            return self.matches[state]
        except IndexError:
            return None

class MenuFunction():
    """any end-of-the-line arbitrary function"""
    def __init__(self):
        self.name = None

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def __str__(self):
        return self.name

class Gun(MenuFunction):
    """
    In theory, allow users to write classes like this which we can tab-complete to run.
    These can be anything.
    """
    def __init__(self):
        self.name = self.__class__.__name__

    @staticmethod
    def reload():
        print("reloading your gun...\n\n\n")

    @classmethod
    def fire(cls):
        print("firing the guns!\n\n")

class Missile(MenuFunction):
    """
    In theory, allow users to write classes like this which we can tab-complete to run.
    These can be anything.
    """
    def __init__(self):
        self.name = self.__class__.__name__

    @staticmethod
    def reload():
        print("reloading your missile launcher...\n\n\n")

    @classmethod
    def status(cls):
        print("missile status stuff......\n\n")

OPTIONS = {'weapons': [{'gun': Gun()}, {'missile': Missile()}], 'anotherthing': ['item1', 'item2'], 'yetanotherthing': ['nothing']}
completer = MyCompleter(options=list(OPTIONS))
readline.set_completer(completer.complete)

class ConfigurationContext():

    def __init__(self, options):
        self.all_options = options
        self.current_options = list(self.all_options)  # starting state
        self.level = None  # current menu level name
        self.stack = []
        self.prompt = None
        self.ready_to_execute = False
        self.executing_class = None
        self.user_request = None
        self.construct_prompt(self.level)

    def construct_prompt(self, level):

        if not self.ready_to_execute:
            self.level = level
        else:
            self.level = self.stack[-1]

        self.current_options = self.get_options(level)
        self.prompt = f"{BASE_PROMPT}({level or ''})#"

        if level not in chain(['', 'exit', None], self.stack):
            # one final check to ensure terminal command options aren't in the prompt.
            if not self.ready_to_execute:
                self.stack.append(level)

        # recurse into the dictionary to grab what we need at our level.
        if self.stack and not self.ready_to_execute:
            ret = self.all_options

            for x in self.stack:
                try:
                    ret = ret[x]
                except TypeError:
                    foo = self.stringify(ret)
                    tgt = foo.index(self.level)
                    # we got to a terminal class. Set the current list of options
                    # as the non-magic exposed properties of that class.
                    # [y for y in dir(x) if not y.startswith('_')]
                    for x in ret[tgt].values():
                        self.current_options = [y for y in dir(x) if not y.startswith('_')]
                        self.ready_to_execute = True
                        self.executing_class = x
                        # import pdb;pdb.set_trace()
                        return
                        # from ast import literal_eval
                        # literal_eval(x.status)
                    # This is a class we can act on.
                    # pass
                    # function_dict = ret[idx]
                    # function_object = list(function_dict.values())[0]

                    # # TODO: cast the object as a str everywhere we need to use it. otherwise, use the object.
                    # from ast import literal_eval
                    # literal_eval(function_object.status)

        if self.ready_to_execute:
            # import pdb;pdb.set_trace()
            # double check that the class being called has that attribute.
            if hasattr(self.executing_class, self.user_request):
                eval(f'{self.executing_class}.{self.user_request}()')
                self.ready_to_execute = False
            #
            # pass

    def stringify(self, iterable):
        return [list(x.keys())[0] if isinstance(x, dict) else x for x in iterable]


    def get_options(self, level):
        """return a list of options for a given level in the options dict
        use the stack to determine where to index into the options dict
        """
        if self.ready_to_execute:
            return self.current_options

        opts = None
        try:
            opts = list(self.all_options[level])
        except KeyError:
            # starting state, or coming back to the root
            opts = list(self.all_options)

        finally:
            # Some items might be dict classes. They all need to become strings.
            # For all options, return the option unless it is a type == dict, then return its 0th
            # key as a string.
            # TODO: this assumes a dict len == 1, which isn't awesome if we want multiple entries
            # return [list(x.keys())[0] if isinstance(x, dict) else x for x in opts]
            return self.stringify(opts)

    def __repr__(self):
        return f"{self.__class__.__name__}(options={self.all_options})"

def main():
    input_ = ""  # default needed for starting state
    ctx = ConfigurationContext(options=OPTIONS)
    print('Welcome to the shellthing tool. Hit tab for commands.\n')
    try:
        while True:
            input_ = input(ctx.prompt)

            if input_ == "exit":
                # go up one level.
                try:
                    ctx.stack.pop()
                except IndexError:
                    # We are at the top of the stack. Exit the program.
                    sys.exit(0)

                try:
                    ctx.construct_prompt(level=ctx.stack[-1])
                except IndexError:
                    # We send you back to the root of the tree.
                    ctx.construct_prompt(level='')

                # set the available tab-complete options.
                # completer.options = ctx.current_options

            elif input_ == "help":
                print("This is some help text\n")
                input_ = ""
            elif input_ == "":
                continue  # They just hit enter, give 'em another prompt.
            elif input_ == "d":
                # DEBUG
                from pprint import pprint
                pprint(vars(ctx))
            elif input_ not in ctx.current_options:
                # continue if they enter a non-option
                print(f'Command not recognized. Maybe try: {ctx.current_options} ?')
                continue
            else:
                # a valid option was selected
                ctx.construct_prompt(input_)

            # set the available tab-complete options.
            completer.options = ctx.current_options
            # import pdb;pdb.set_trace()
            ctx.user_request = input_

    except KeyboardInterrupt:
        sys.exit(255)

if __name__ == "__main__":
    main()
