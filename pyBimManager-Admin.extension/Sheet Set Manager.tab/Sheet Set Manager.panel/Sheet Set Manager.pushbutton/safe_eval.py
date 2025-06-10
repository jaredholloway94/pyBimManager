import ast


ALLOWED_METHODS = {
    'upper',
    'lower',
    'strip',
    'replace',
    'capitalize',
    'title',
    'split',
    'join',
    'zfill',
    'ljust',
    'rjust',
    'index',
    }

ALLOWED_NAMES = {
    'sheet_group_name',
    'level_name',
    'level_counter',
    'scope_box_name',
    'scope_box_counter',
    'sheet_counter',
    'view_family_name',
    'view_type_name'
    }

ALLOWED_BUILTINS = {
    'str',
    'int',
}


class SafeEvalVisitor(ast.NodeVisitor):
    def visit_Expression(self, node):
        self.visit(node.body)

    def visit_Name(self, node):
        if node.id not in ALLOWED_NAMES and node.id not in ALLOWED_BUILTINS:
            raise ValueError(f"Use of name '{node.id}' is not allowed")

    def visit_Attribute(self, node):
        self.visit(node.value)
        if node.attr not in ALLOWED_METHODS:
            raise ValueError(f"Method '{node.attr}' is not allowed")

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name):
            if node.func.id not in ALLOWED_BUILTINS:
                raise ValueError(f"Use of function '{node.func.id}' is not allowed")
        elif isinstance(node.func, ast.Attribute):
            self.visit(node.func)
        else:
            raise ValueError("Unsupported function call type")
        for arg in node.args:
            self.visit(arg)

    def visit_BinOp(self, node):
        if not isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod)):
            raise ValueError("Unsupported binary operation")
        self.visit(node.left)
        self.visit(node.right)

    def visit_Subscript(self, node):
        self.visit(node.value)
        self.visit(node.slice)

    def visit_Slice(self, node):
        if node.lower: self.visit(node.lower)
        if node.upper: self.visit(node.upper)
        if node.step: self.visit(node.step)

    def visit_Index(self, node):  # For Python < 3.9
        self.visit(node.value)

    def visit_Constant(self, node):
        if not isinstance(node.value, (str, int, float)):
            raise ValueError("Only string, integer, or float constants are allowed")

    def visit_Num(self, node):  # Python < 3.8
        pass

    def visit_Str(self, node):  # Python < 3.8
        pass

    def visit_UnaryOp(self, node):
        if isinstance(node.op, ast.USub):  # Allow negative numbers
            self.visit(node.operand)
        else:
            raise ValueError("Only unary minus is allowed")

    def generic_visit(self, node):
        raise ValueError(f"Unsupported operation: {type(node).__name__}")
    

def safe_eval(expr, context):
    tree = ast.parse(expr, mode='eval')
    SafeEvalVisitor().visit(tree)
    return eval(compile(tree, '<string>', mode='eval'), {}, context)