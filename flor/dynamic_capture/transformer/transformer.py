import ast
import astor
from florist.generator import Assign, BoolExp, Raise, Return, FuncDef, Loop

class Transformer(ast.NodeTransformer):

    def __init__(self, filepath=''):
        super().__init__()
        self.active = False
        self.filepath = filepath
        self.classname = None
        self.fd = None

    def visit_ClassDef(self, node):
        self.classname = node.name
        new_node = self.generic_visit(node)
        self.classname = None
        return new_node

    def visit_FunctionDef(self, node):
        if '__' != node.name[0:2] or node.name == '__init__':
            # ONLY WRAP PUBLIC METHODS TO AVOID STACK OVERFLOW
            self.active = True
            prev = self.fd
            self.fd = FuncDef(node, self.filepath, self.classname)
            heads = self.fd.parse_heads()
            foot = self.fd.parse_foot()
            new_node = self.generic_visit(node)
            heads.extend(new_node.body)
            new_node.body = heads
            if isinstance(new_node.body[-1], ast.Pass):
                new_node.body.pop()
            new_node.body.append(foot)
            self.fd = prev
            self.active = False
            return new_node
        else:
            return node

    def visit_If(self, node):
        if self.active:
            node.body.insert(0, self.visit(BoolExp(node.test).parse(True)))
            node.orelse.insert(0, self.visit(BoolExp(node.test).parse(False)))
        return self.generic_visit(node)

    def visit_For(self, node):
        if self.active:
            loop = Loop(node)
            node.body.insert(0, self.visit(loop.parse_start()))
            node.body.append(self.visit(loop.parse_end()))
        return self.generic_visit(node)

    def visit_While(self, node):
        if self.active:
            loop = Loop(node)
            node.body.insert(0, self.visit(loop.parse_start()))
            node.body.append(self.visit(loop.parse_end()))
        return self.generic_visit(node)

    def visit_Return(self, node):
        nodes_module = Return(node).parse()
        nodes_module.body.insert(-1, self.visit(self.fd.parse_foot()))
        if len(nodes_module.body) <= 2:
            return nodes_module.body
        ret_stmt = nodes_module.body.pop()
        nodes_module = self.generic_visit(nodes_module)
        nodes_module.body.append(ret_stmt)
        return nodes_module.body

    def generic_visit(self, node):
        if self.active:
            for field, old_value in ast.iter_fields(node):
                if isinstance(old_value, list):
                    new_values = []
                    for value in old_value:
                        if isinstance(value, ast.Raise):
                            r = self.visit(Raise(value).parse())
                            new_values.append(r)
                        elif isinstance(value, ast.Return):
                            values = self.visit(value)
                            assert values and isinstance(values, list)
                            new_values.extend(values)
                            continue
                        if isinstance(value, ast.AST):
                            value = self.visit(value)
                            if value is None:
                                continue
                            elif not isinstance(value, ast.AST):
                                new_values.extend(value)
                                continue
                        new_values.append(value)
                        if isinstance(value, ast.Assign) or \
                                isinstance(value, ast.AugAssign) or \
                                isinstance(value, ast.AnnAssign):
                            # OUTPUT ASSIGN STATEMENT
                            value = self.visit(Assign(value).parse())
                            new_values.append(value)
                    old_value[:] = new_values
                elif isinstance(old_value, ast.AST):
                    new_node = self.visit(old_value)
                    if new_node is None:
                        delattr(node, field)
                    else:
                        setattr(node, field, new_node)
            return node
        else:
            return super().generic_visit(node)