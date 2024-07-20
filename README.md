# Sharh

A minimal DSL that compiles to an object compatible with [api7/lua-resty-expr](https://github.com/api7/lua-resty-expr).

## Installation
```
$ pip install sharh
```

## Synopsis
```py
from sharh.parser import parse

tree = parse("""http.headers.user_agent contains 'curl'
			    and (ip.addr in [1.2.3.4, 5.6.7.8/24] or ip.geoip.asn  10)""")
tree.to_expr_notation()
```
Result:
```
['OR',
 ['AND',
  ['http.headers.user_agent', '~~', 'curl'],
  ['ip.addr', 'ipmatch', ['1.2.3.4', '5.6.7.8/24']]],
 ['AND',
  ['http.headers.user_agent', '~~', 'curl'],
  ['ip.geoip.asn', '~=', '10']]]
```

Please Note:
 - The result is always in [disjunctive normal form](https://en.wikipedia.org/wiki/Disjunctive_normal_form).
 - In openresty, you can't directly use ngx.var for evaluation. You should provide the context with variables named according to this DSL convention. (e.g. provide a table with `ip.addr`  key instead of `remote_addr`)
 
## Variables
|**key**|**type**|
|-|-|
|http.method|string|
|http.version|string|
|http.secure|string|
|http.headers[*key*]|string|
|http.headers.user_agent|string|
|http.headers.x_forwarded_for|string|
|http.headers.referrer|string|
|http.headers|list\<string\>|
|device|string|
|ip.geoip.country|string|
|ip.geoip.continent|string|
|ip.addr|IPv4|
|ip.geoip.asn|number|

## Operators
|**operator**|**description**|**example**|
|-|-|-|
|==|equals|*ip.addr == 127.0.0.1*|
|!=|not equals|*http.headers.user_agent != 'curl/8.8'*|
|in|exists in right-hand side list| *ip.geoip.asn in [123, 456]*|
|not in|doesn't exist in right-hand side list|*ip.geoip.asn not in [123, 456]*
|has|contains right-hand side item (only compatible with *list* type|*http.headers has 'user_agent'*|
|not has|doesn't contain right-hand side item (only compatible with *list* type|*http.headers not has 'user_agent'*|
|contains|contains right-hand side string (only compatible with *string* type|*http.header.user_agent contains 'curl'*|
|not contains|doesn't contain right-hand side string (only compatible with *string* type|*http.header.user_agent not contains 'curl'*|

## Expressions
### Grammar
Each expression is a string of the following format:
```
left operator right
```
Expressions can be combined using *and*, *or* or parentheses:

```
expr1 and (expr2 or expr3)
```

### Notes
* Right-hand side value for strings should be surrounded by single quoutes (e.g. `'test'`)
* In case of *in* and *not in* operators, right-hand side value must be a list of values of related type:
	* `[1, 2, 3]` for number type
	* `['test1', 'test2', 'test3']` for string type
	* `[1.2.3.4/24, 4.5.6.7]` for IPv4 type (only with *in*/*not in* operator, each list item can be in CIDR format)
