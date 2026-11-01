"""Retain pinned original acquisition logic; replace only PIL display blocks.

The source is validated by the normal app source guards before dispatch. This
additional structural gate fails closed if its drawing boundaries change.
"""
import ast
import copy

def acquisition_loop(source,namespace):
    tree=ast.parse(source)
    classes=[node for node in tree.body if isinstance(node,ast.ClassDef) and node.name=='ToolsImageEntropyLivePreviewScreen']
    if len(classes)!=1:raise ValueError('Missing original entropy screen')
    methods=[node for node in classes[0].body if isinstance(node,ast.FunctionDef) and node.name=='_run']
    if len(methods)!=1:raise ValueError('Missing original acquisition loop')
    return _compile(methods[0],namespace)

def acquisition_method(source,namespace):
    """Parse just the guarded original method, avoiding the whole GUI module AST."""
    tree=ast.parse(source)
    if len(tree.body)!=1 or not isinstance(tree.body[0],ast.FunctionDef) or tree.body[0].name!='_run':raise ValueError('Unexpected acquisition method source')
    return _compile(tree.body[0],namespace)

def _compile(original,namespace):
    method=copy.deepcopy(original);method.decorator_list=[]
    class PresentationOnly(ast.NodeTransformer):
        blocks=0;fonts=0
        def visit_With(self,node):
            if len(node.items)==1 and ast.unparse(node.items[0].context_expr)=='self.renderer.lock':
                self.blocks+=1
                if self.blocks==1:
                    return ast.copy_location(ast.Expr(value=ast.Call(func=ast.Attribute(value=ast.Name(id='self',ctx=ast.Load()),attr='_lvgl_preview',ctx=ast.Load()),args=[ast.Name(id='frame',ctx=ast.Load()),ast.Name(id='entropy_frame',ctx=ast.Load()),ast.Call(func=ast.Name(id='len',ctx=ast.Load()),args=[ast.Name(id='preview_images',ctx=ast.Load())],keywords=[])],keywords=[])),node)
                return ast.copy_location(ast.Pass(),node)
            return self.generic_visit(node)
        def visit_Assign(self,node):
            if len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id=='instructions_font':
                if not ast.unparse(node.value).startswith('Fonts.get_font('):raise ValueError('Unexpected entropy display font expression')
                self.fonts+=1
                return ast.copy_location(ast.Pass(),node)
            return self.generic_visit(node)
    adapter=PresentationOnly();method=adapter.visit(method)
    if (adapter.blocks,adapter.fonts)!=(3,1):raise ValueError('Original entropy presentation structure changed')
    for node in ast.walk(method):
        if isinstance(node,ast.Attribute) and isinstance(node.value,ast.Name) and node.value.id=='self' and node.attr=='renderer':raise ValueError('Unreviewed entropy drawing operation')
    from dependency_policy import bind_original_pillow
    module=ast.fix_missing_locations(bind_original_pillow(ast.Module(body=[method],type_ignores=[]),namespace));local={}
    exec(compile(module,'<pinned entropy acquisition; native presentation>','exec'),namespace,local)
    return local['_run']
