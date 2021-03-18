grammar Rddl;

rddlDoc
  : domain? nonFluents* instance*
  ;

domain
  : 'domain' domainNAME '{' requirements? types? pvariables cpfs reward
  stateInvariants? actionPreconditions? '}'    
  ;

domainName
  : NAME
  ;

requirements
  : 'requirements' '=' '{' REQUIREMENT (',' REQUIREMENT)* '}' ';'
  ;

types
  : 'types' '{' (object | enumerated)+ '}' ';'
  ;

object
  : NAME ':' 'object' ';'
  ;

enumerated
  : NAME ':' '{' ENUM (',' ENUM)* '}' ';'
  ;

pvariables
  : 'pvariables' '{' pv* '}' ';'
  ;

pv
  : NAME ('(' NAME (',' NAME)* ')')? ':' '{' VAR_TYPE ',' (NAME | VAL_TYPE) 
  ',' 'default' '=' (NUM | BOOL | ENUM) '}' ';'
  ;

cpfs
  : 'cpfs' '{' stat* '}' ';'
  ;

stat 
  : (NAME | S_VAR) ('(' PARAM (',' PARAM)* ')')? ('=' expr)? ';' 
  ;

arith_expr 
  : arith_expr '/' arith_expr
  | arith_expr '*' arith_expr
  | arith_expr '+' arith_expr
  | arith_expr '-' arith_expr
  | arith_expr '%' arith_expr
  | arith_expr '**' arith_expr
  | '!' arith_expr
  | '(' arith_expr ')'
  | '[' arith_expr ']'
  | expr '<' expr
  | expr '>' expr
  | expr '<=' expr
  | expr '>=' expr
  | expr '==' expr
  | expr '~=' expr
  | expr '^' expr
  | expr '|' expr
  | expr '=>' expr
  | expr '<=>' expr
  | '~' expr
  | '!' expr
  | '(' expr ')'
  | '[' expr ']'
  | sum
  | product
  | e_quant
  | u_quant
  | conditional
  | switch 
  | dist
  | NUM
  | NAME ('(' PARAM (',' PARAM)* ')')? 
  | BOOL
  | ENUM
  ;

sum 
  : 'sum_' '{' PARAM ':' NAME (',' PARAM ':' NAME)* '}' 
  '[' expr ']' ';'
  ;

product 
  : 'prod_' '{' PARAM ':' NAME (',' PARAM ':' NAME)* '}' 
  '[' expr ']' ';'
  ;

e_quant 
  : 'exists_' '{' PARAM ':' NAME (',' PARAM ':' NAME)* '}' 
  '[' expr ']' ';'
  ;

u_quant 
  : 'forall_' '{' PARAM ':' NAME (',' PARAM ':' NAME)* '}' 
  '[' expr ']' ';'
  ;


