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
