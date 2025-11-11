const fs = require('fs');
const parser = require('@babel/parser');

// Helper function to get docstrings
function getDocstring(node) {
  const comments = node.leadingComments;
  if (comments && comments.length > 0) {
    const lastComment = comments[comments.length - 1];
    if (lastComment.type === 'CommentBlock' && lastComment.value.startsWith('*')) {
      // It's a JSDoc-style comment block
      return lastComment.value.replace(/(\r\n|\n|\r)/gm, '\n').replace(/^\* ?/gm, '').trim();
    }
  }
  return null;
}

// Helper to get function/method details
// --- MODIFIED: This now handles ObjectPattern destructuring ---
function getFunctionDetails(node) {
  const params = [];
  for (const p of node.params) {
    if (p.type === 'Identifier') {
      params.push(p.name);
    } else if (p.type === 'AssignmentPattern' && p.left.type === 'Identifier') {
      params.push(p.left.name);
    } else if (p.type === 'RestElement' && p.argument.type === 'Identifier') {
      params.push(`...${p.argument.name}`);
    } else if (p.type === 'ObjectPattern') {
      // Handle { name, age }
      for (const prop of p.properties) {
        if (prop.type === 'ObjectProperty' && prop.key.type === 'Identifier') {
          params.push(prop.key.name);
        } else if (prop.type === 'RestElement' && prop.argument.type === 'Identifier') {
          params.push(`...${prop.argument.name}`);
        }
      }
    } else {
      params.push('?');
    }
  }

  let returnType = null;
  if (node.returnType && node.returnType.type === 'TSTypeAnnotation') {
    const type = node.returnType.typeAnnotation;
    if (type.type === 'TSStringKeyword') returnType = 'string';
    else if (type.type === 'TSNumberKeyword') returnType = 'number';
    else if (type.type === 'TSBooleanKeyword') returnType = 'boolean';
    else if (type.type === 'TSVoidKeyword') returnType = 'void';
    else if (type.type === 'TSAnyKeyword') returnType = 'any';
    // This is a simplified type extractor
  }

  return { params, returnType };
}

// Main parsing function
function parseFile(filePath) {
  const elements = [];
  const imports = [];

  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    const ast = parser.parse(content, {
      sourceType: 'module',
      plugins: ['typescript', 'jsx'],
      errorRecovery: true, // Try to parse even with errors
    });

    for (const node of ast.program.body) {
      // 1. Find Imports
      if (node.type === 'ImportDeclaration' || node.type === 'ExportAllDeclaration' || node.type === 'ExportNamedDeclaration') {
        if (node.source) {
          imports.push(node.source.value);
        }
      }

      // 2. Find Functions (FunctionDeclaration)
      if (node.type === 'FunctionDeclaration' || (node.type === 'ExportNamedDeclaration' && node.declaration?.type === 'FunctionDeclaration') || (node.type === 'ExportDefaultDeclaration' && node.declaration?.type === 'FunctionDeclaration')) {
        const funcNode = node.declaration || node;
        const { params, returnType } = getFunctionDetails(funcNode);
        elements.push({
          type: 'function',
          name: funcNode.id ? funcNode.id.name : 'defaultExport',
          start_line: funcNode.loc.start.line,
          end_line: funcNode.loc.end.line,
          docstring: getDocstring(node),
          parameters: params,
          return_type: returnType,
        });
      }

      // --- NEW: Find exported arrow functions (e.g., export const MyComponent = () => ...) ---
      if (node.type === 'ExportNamedDeclaration' && node.declaration?.type === 'VariableDeclaration') {
        for (const declarator of node.declaration.declarations) {
          if (declarator.id.type === 'Identifier' && declarator.init?.type === 'ArrowFunctionExpression') {
            const funcNode = declarator.init;
            const { params, returnType } = getFunctionDetails(funcNode);

            elements.push({
              type: 'function',
              name: declarator.id.name,
              start_line: funcNode.loc.start.line,
              end_line: funcNode.loc.end.line,
              docstring: getDocstring(node), // Docstring is on the export
              parameters: params,
              return_type: returnType,
            });
          }
        }
      }
      // --- END NEW ---

      // 3. Find Classes
      if (node.type === 'ClassDeclaration' || (node.type === 'ExportNamedDeclaration' && node.declaration?.type === 'ClassDeclaration') || (node.type === 'ExportDefaultDeclaration' && node.declaration?.type === 'ClassDeclaration')) {
        const classNode = node.declaration || node;
        const baseClasses = classNode.superClass ? [classNode.superClass.name] : [];

        elements.push({
          type: 'class',
          name: classNode.id ? classNode.id.name : 'defaultExport',
          start_line: classNode.loc.start.line,
          end_line: classNode.loc.end.line,
          docstring: getDocstring(node),
          base_classes: baseClasses,
        });

        // 4. Find Methods within Classes
        for (const bodyNode of classNode.body.body) {
          if (bodyNode.type === 'ClassMethod' || bodyNode.type === 'ClassPrivateMethod') {
            const { params, returnType } = getFunctionDetails(bodyNode);

            let name = 'computed'; // Default for computed properties
            if (bodyNode.key.type === 'Identifier') {
              name = bodyNode.key.name; // For constructor, public/private methods
            } else if (bodyNode.key.type === 'PrivateName') {
              name = bodyNode.key.id.name; // For private fields #myMethod
            }

            elements.push({
              type: 'method',
              name: name,
              start_line: bodyNode.loc.start.line,
              end_line: bodyNode.loc.end.line,
              docstring: getDocstring(bodyNode),
              parameters: params,
              return_type: returnType,
            });
          }
        }
      }
    }

    // Output JSON to stdout
    console.log(JSON.stringify({ elements, imports }));

  } catch (error) {
    // Output error to stderr and exit
    console.error(`Error parsing ${filePath}: ${error.message}`);
    process.exit(1);
  }
}

// Get file path from command line argument
const filePath = process.argv[2];
if (!filePath) {
  console.error('Error: No file path provided.');
  process.exit(1);
}

parseFile(filePath);