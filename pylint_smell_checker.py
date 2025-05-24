import astroid
from pylint.checkers import BaseChecker


class HardcodedModelDownloadChecker(BaseChecker):
    name = 'hardcoded-model-download-checker'
    msgs = {
        'C9003': (
            'Hardcoded model version or URL detected. Use configuration or environment variables instead.',
            'hardcoded-model-download',
            'Avoid hardcoding model version or download URL strings.'
        ),
    }

    def visit_assign(self, node):
        """Detect hardcoded model version or URL assignment."""
        try:
            # Check for hardcoded model version like MODEL_VERSION = "v0.0.9"
            if isinstance(node.value, astroid.Const) and isinstance(node.value.value, str):
                # Check for variable names like MODEL_VERSION
                if hasattr(node.targets[0], 'name') and "version" in node.targets[0].name.lower():
                    self.add_message('hardcoded-model-download', node=node)
            # Check for BASE_URL assignments involving GitHub or HTTP(S) URLs
            if isinstance(node.value, astroid.BinOp) and isinstance(node.value.op, str) and node.value.op == '+':
                if isinstance(node.value.left, astroid.Const) and "http" in node.value.left.value:
                    self.add_message('hardcoded-model-download', node=node)
            # Detect usage of full f-string BASE_URL format
            if isinstance(node.value, astroid.JoinedStr):
                for part in node.value.values:
                    if isinstance(part, astroid.Const) and "http" in part.value:
                        self.add_message('hardcoded-model-download', node=node)
        except Exception:
            pass


class MissingDataValidationChecker(BaseChecker):
    name = 'missing-data-validation-checker'
    msgs = {
        'C9004': (
            'Variable "data" used without checking for emptiness or existence.',
            'missing-data-validation',
            'Ensure input data is validated before use to avoid crashes or undefined behavior.',
        ),
    }

    def visit_functiondef(self, node):
        """Check functions for usage of 'data' without proper validation."""
        try:
            has_data_usage = False
            has_validation = False
            func_source = node.as_string()
            # Check for data usage (excluding assignments and validation checks)
            for stmt in node.body:
                for name_node in stmt.nodes_of_class(astroid.Name):
                    if name_node.name == 'data':
                        # Skip if this is part of an assignment target
                        parent = name_node.parent
                        if isinstance(parent, astroid.Assign) and name_node in parent.targets:
                            continue
                        # Skip if this is part of a validation check
                        if self._is_validation_usage(name_node):
                            has_validation = True
                        else:
                            has_data_usage = True
            # Look for common validation patterns in the source
            validation_patterns = [
                'if not data:',
                'if data is None:',
                'if len(data) == 0:',
                'if not len(data):',
                'if data == None:',
                'if data == []:',
                'if data == {}:',
            ]
            for pattern in validation_patterns:
                if pattern in func_source:
                    has_validation = True
                    break
            if has_data_usage and not has_validation:
                self.add_message('missing-data-validation', node=node)
        except Exception:
            pass

    def _is_validation_usage(self, name_node):
        """Check if this usage of 'data' is in a validation context."""
        parent = name_node.parent
        # Check if it's in a unary not operation: not data
        if isinstance(parent, astroid.UnaryOp) and parent.op == 'not':
            return True
        # Check if it's in a comparison: data is None, data == None, etc.
        if isinstance(parent, astroid.Compare):
            return True
        # Check if it's in a len() call for validation
        if isinstance(parent, astroid.Call) and isinstance(parent.func, astroid.Name):
            if parent.func.name == 'len':
                return True
        return False


def register(linter):
    linter.register_checker(HardcodedModelDownloadChecker(linter))
    linter.register_checker(MissingDataValidationChecker(linter))
