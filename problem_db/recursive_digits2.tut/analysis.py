class CodeVisitor(TutorialNodeVisitor):
    def __init__(self):
        super().__init__()

        self.has_recursive_call = False

        self.checks_arg1_in_base_case = False

    def visit_Call(self, node):
        super().visit_Call(node)

        if TutorialNodeVisitor.identifier(node.func) == 'dec2base':
            self.has_recursive_call = True

    def visit_If(self, node):
        super().visit_If(node)

        arg = self.functions['dec2base'].args[0]
        if arg is not None:
            self.checks_arg1_in_base_case = \
                    arg in TutorialNodeVisitor.involved_identifiers(node)


class RecursiveDigits2Analyser(CodeAnalyser):
    def _analyse(self):
        if not self.visitor.functions['dec2base'].is_defined:
            self.add_error('dec2base is not defined')
        if not self.visitor.has_recursive_call:
            self.add_error('dec2base does not appear to be recursive')
        if not self.visitor.checks_arg1_in_base_case:
            self.add_warning('Your base case should probably check {}'.format(self.visitor.functions['dec2base'].args[0]))


ANALYSER = RecursiveDigits2Analyser(CodeVisitor)