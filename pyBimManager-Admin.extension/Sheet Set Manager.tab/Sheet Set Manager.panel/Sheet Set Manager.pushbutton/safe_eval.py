import ast

# Safe list of allowed built-in functions/methods
ALLOWED_METHODS = {'upper', 'lower', 'strip', 'replace', 'capitalize', 'title', 'split'}

# Allowed variable names
ALLOWED_NAMES = {'level_name', 'scope_box_name'}

class SafeEvalVisitor(ast.NodeVisitor):
    def visit_Expression(self, node):
        self.visit(node.body)

    def visit_Name(self, node):
        if node.id not in ALLOWED_NAMES:
            raise ValueError(f"Use of variable '{node.id}' is not allowed")
    
    def visit_Attribute(self, node):
        self.visit(node.value)
        if not isinstance(node.value, ast.Name):
            raise ValueError("Chained attributes are not allowed")
        if node.attr not in ALLOWED_METHODS:
            raise ValueError(f"Method '{node.attr}' is not allowed")

    def visit_Call(self, node):
        if not isinstance(node.func, ast.Attribute):
            raise ValueError("Only method calls are allowed")
        self.visit(node.func)
        for arg in node.args:
            self.visit(arg)

    def visit_BinOp(self, node):
        if not isinstance(node.op, (ast.Add, ast.Mod)):
            raise ValueError("Only string concatenation or formatting is allowed")
        self.visit(node.left)
        self.visit(node.right)

    def visit_Subscript(self, node):
        self.visit(node.value)
        self.visit(node.slice)

    def visit_Index(self, node):
        self.visit(node.value)

    def visit_Slice(self, node):
        if node.lower: self.visit(node.lower)
        if node.upper: self.visit(node.upper)
        if node.step: self.visit(node.step)

    def visit_Constant(self, node):
        if not isinstance(node.value, str):
            raise ValueError("Only string constants are allowed")

    def visit_Str(self, node):  # For Python < 3.8
        pass

    def generic_visit(self, node):
        raise ValueError(f"Unsupported operation: {type(node).__name__}")

def safe_eval(expr, context):
    tree = ast.parse(expr, mode='eval')
    SafeEvalVisitor().visit(tree)
    return eval(compile(tree, '<string>', mode='eval'), {}, context)