/**
 * TrimPath Query. Release 1.1.13.
 * Copyright (C) 2004 - 2007 TrimPath.
 * 
 * This program is free software; you can redistribute it and/or 
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 * 
 * This program is distributed WITHOUT ANY WARRANTY; without even the 
 * implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
 * See the GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
 */
if (typeof(TrimPath) == 'undefined')
    TrimPath = {};

(function() { // Using a closure to keep global namespace clean.
    var theEval   = eval;
    var theString = String;
    var theArray  = Array;

    if (TrimPath == null)
        TrimPath = new Object();
    if (TrimPath.TEST == null)
        TrimPath.TEST = new Object(); // For exposing to testing only.

    var arrayUniq = function(arr) {
        var result = [];
        for (var i = 0; i < arr.length; i++) {
            if (arrayInclude(result, arr[i]) == false)
                result.push(arr[i]);
        }
        return result;
    }

    var arrayInclude = function(arr, val) {
        for (var j = 0; j < arr.length; j++) {
            if (arr[j] == val)
                return true;
        }
        return false;
    }

    var arrayCompact = function(arr) {
        var result = [];
        for (var i = 0; i < arr.length; i++)
            if (arr[i] != null)
                result.push(arr[i])
        return result;
    }

    var simpleJson = function(fields, values) { // The fields and values are arrays of strings.
        var json = [ '{' ];
        for (var i=0; i<fields.length; i++) {
            if (i > 0)
                json.push(',');
            json.push(fields[i]);
            json.push(':');
            if (values[i]) {
                json.push('"');
                json.push(values[i].replace(/(["\\])/g, '\\$1').replace(/\r/g, '').replace(/\n/g, '\\n'));
                json.push('"');
            } else
                json.push(null);
        }
        json.push('}');
        return json.join('');
    }
    
    var hashKeys = function(object) {
        var keys = [];
        for (var property in object)
          keys.push(property);
        return keys;
    }

    var hashValues = function(object) {
        var values = [];
        for (var property in object)
          values.push(object[property]);
        return values;
    }

    var strip = function(str) {
        return str.replace(/^\s+/, '').replace(/\s+$/, '');
    }

    TrimPath.makeQueryLang_etc = {}; 
    TrimPath.makeQueryLang_etc.Error = function(message, stmt) { // The stmt can be null, a String, or an Object.
        this.message = message; 
        this.stmt    = stmt;
    }
    TrimPath.makeQueryLang_etc.Error.prototype.toString = function() { 
        return ("TrimPath query Error in " + (this.stmt != null ? this.stmt : "[unknown]") + ": " + this.message);
    }

    var TODO  = function() { throw "currently unsupported"; };
    var USAGE = function() { throw "incorrect keyword usage"; };

    var QueryLang = function() {};

    TrimPath.makeQueryLang = function(tableInfos, etc) {
        if (etc == null)
            etc = TrimPath.makeQueryLang_etc;

        var aliasArr = []; // Used after SELECT to clean up the queryLang for reuse.
        var aliasReg = function(aliasKey, scope, obj) {
            if (scope[aliasKey] != null)
                throw new etc.Error("alias redefinition: " + aliasKey);
            aliasArr.push({ aliasKey: aliasKey, scope: scope, orig: scope[aliasKey] });
            scope[aliasKey] = obj;
            return obj;
        }

        var queryLang = new QueryLang();

        var checkArgs = function(args, minLength, maxLength, name, typeCheck) {
            args = cleanArray(args);
            if (minLength == null)
                minLength = 1;
            if (args == null || args.length < minLength)
                throw new etc.Error("not enough arguments for " + name);
            if (maxLength != null && args.length > maxLength)
                throw new etc.Error("too many arguments for " + name);
            if (typeCheck != null)
                for (var k in args)
                    if (typeof(args[k]) != "function" && // Ignore functions because other libraries like to extend Object.prototype.
                        args[k] instanceof typeCheck == false)
                        throw new etc.Error("wrong type for " + args[k] + " to " + name);
            return args;
        }
        
        var sql_date_to_js_date = function(data) {
            if(typeof data == "string" && data.match(/\d{4}-\d{1,2}-\d{1,2}/)) {
                var dateArr = data.match(/\d{4}-\d{1,2}-\d{1,2}/)[0].split('-');
                var date = new Date(parseInt(dateArr[0], 10), (parseInt(dateArr[1], 10)-1), parseInt(dateArr[2], 10));
                return date;
            }
            return data;
        }
        
        var data_insertion = function(table_info, field_name, data, column_ref) {
            if(table_info[field_name]) {
                var data = eval(data);
                if(table_info[field_name].type && table_info[field_name].type == 'Number')
                    data = Number(data, 10);
                else if(table_info[field_name].type && table_info[field_name].type == 'Date')
                    data = sql_date_to_js_date(data);
                column_ref[field_name] = data;
            }
        }
    
        var NodeType = { // Constructor functions for SELECT statement tree nodes.
            select : function(args) {
                var columns = [];
                var nodes = { from : null, where : null, groupBy : null, having : null, orderBy : null,
                              limit : null };

                for (var i = 0; i < args.length; i++) { // Parse args into columns and nodes.
                    var arg = args[i];
                    var argIsNode = false;
                    for (var nodeTypeName in nodes) {
                        if (arg instanceof NodeType[nodeTypeName]) {
                            if (nodes[nodeTypeName] != null)
                                throw new etc.Error("too many " + nodeTypeName.toUpperCase() + " clauses");
                            nodes[nodeTypeName] = arg;
                            argIsNode = true;
                            break;
                        }
                    }
                    if (argIsNode == false) // Then the arg must be a column.
                        columns.push(arg);
                }
                columns = checkArgs(columns, 1, null, "COLUMNS");
                if (nodes.from == null)
                    throw new etc.Error("missing FROM clause");

                var joinDriver        = null;
                var joinFilter        = null;
                var whereFilter       = null;
                var columnConvertor   = null;
                var orderByComparator = null;
                var groupByCalcValues = null;
                var havingFilter      = null;

                var typeConverter = function(results) {
                    for(var i=0; i<results.length; i++) {
                        var result = results[i];
                        for(var attr in result) {
                            var value = result[attr];
                            if(value instanceof Date)
                                results[i][attr] = dateToString(value);
                        }
                    }
                }

                this.prepareFilter = function() {
                    if (joinDriver == null)
                        joinDriver = compileJoinDriver(nodes.from.tables);
                    if (joinFilter == null)
                        joinFilter = compileFilter(compileFilterForJoin, nodes.from.tables);
                    if (whereFilter == null)
                        whereFilter = compileFilter(compileFilterForWhere, nodes.from.tables, nodes.where != null ? nodes.where.exprs : null);
                    if (groupByCalcValues == null && nodes.groupBy != null)
                        groupByCalcValues = compileGroupByCalcValues(nodes.from.tables, nodes.groupBy.exprs);
                    if (havingFilter == null && nodes.having != null)
                        havingFilter = compileFilter(compileFilterForWhere, [], nodes.having.exprs, { aliasOnly : true });
                    if (columnConvertor == null)
                        columnConvertor = compileColumnConvertor(nodes.from.tables, columns);
                    if (orderByComparator == null && nodes.orderBy != null)
                        orderByComparator = compileOrderByComparator(nodes.orderBy.exprs);
                }

                /* params is a list of parameters including:
                 * with_table: if set to true, the results will include table_name+'.'+field_name
                 * return_reference: used by update and delete queries, if set to true, returns reference of data rather than copies,
                 *                   returns the result of the joinDriver
                 */
                this.filter = function(dataTables, bindings, params) {
                    this.prepareFilter();
                    if (bindings == null)
                        bindings = {};
                    if (params == null)
                        params = {};

                    var resultOfFromWhere = joinDriver(dataTables, joinFilter, whereFilter, bindings);

                    if (groupByCalcValues != null) {
                        for (var i = 0; i < resultOfFromWhere.length; i++)
                            resultOfFromWhere[i].groupByValues = groupByCalcValues.apply(null, resultOfFromWhere[i]);
                        resultOfFromWhere.sort(groupByComparator);
                    }
                    
                    if (params.return_reference)
                        return resultOfFromWhere;
                    
                    var groupByAccum = {}; // Accumlation area for aggregate functions.
                    var groupByFuncs = { 
                        SUM : function(key, val) { 
                            groupByAccum[key] = zeroDefault(groupByAccum[key]) + zeroDefault(val);
                            return groupByAccum[key];
                        }, 
                        COUNT : function(key) { 
                            groupByAccum[key] = zeroDefault(groupByAccum[key]) + 1;
                            return groupByAccum[key];
                        },
                        AVG : function(key, val) { 
                            return groupByFuncs.SUM(key, val) / groupByFuncs.COUNT("_COUNT" + key);
                        }
                    };

                    var result = [], prevItem = null, currItem;
                    for (var i = 0; i < resultOfFromWhere.length; i++) {
                        currItem    = resultOfFromWhere[i];
                        currItem[0] = groupByFuncs;
                        if (prevItem != null &&
                            groupByComparator(prevItem, currItem) != 0) {
                            if (havingFilter == null ||
                                havingFilter(prevItem.record) == true)
                                result.push(prevItem.record);
                            groupByAccum = {};
                        }
                        currItem.record = columnConvertor.apply(null, currItem.concat([params.with_table])); // Must visit every item to calculate aggregates.
                        prevItem = currItem;
                    }
                    if (prevItem != null &&
                        (havingFilter == null ||
                         havingFilter(prevItem.record) == true))
                        result.push(prevItem.record);

                    if (orderByComparator != null)
                        result.sort(orderByComparator);
                    if (nodes.limit != null) {
                        if (nodes.limit.total == 0)
                            return [];
                        var start = (nodes.limit.offset != null ? nodes.limit.offset : 0);
                        result = result.slice(start, start + (nodes.limit.total > 0 ? nodes.limit.total : result.length));
                    }
                    
                    typeConverter(result)
                    return result;
                }
                
                setSSFunc(this, function() {
                    var sqlArr = [ "SELECT", map(columns, toSqlWithAlias).join(", "), nodes.from.toSql() ];
                    if (nodes.where != null)
                        sqlArr.push(nodes.where.toSql());
                    if (nodes.groupBy != null)
                        sqlArr.push(nodes.groupBy.toSql());
                    if (nodes.having != null)
                        sqlArr.push(nodes.having.toSql());
                    if (nodes.orderBy != null)
                        sqlArr.push(nodes.orderBy.toSql());
                    if (nodes.limit != null)
                        sqlArr.push(nodes.limit.toSql());
                    return sqlArr.join(" ");
                });

                for (var i = 0; i < aliasArr.length; i++) { // TODO: In nested select, parent's aliases are incorrectly reset.
                    var aliasItem = aliasArr[i];
                    aliasItem.scope[aliasItem.aliasKey] = aliasItem.orig; 
                }
                aliasArr = [];
            },
            insert  : function(args) {
                var table_info = args[0];
                var object = args[1];
                this.filter  = function(dataTables, bindings) {
                    var table_name = table_info['.name'];
                    if(!dataTables[table_name])
                        dataTables[table_name] = [];
                    dataTables[table_name].push({});
                    for(var field_name in object) {
                        data_insertion(table_info, field_name, object[field_name], dataTables[table_name][dataTables[table_name].length-1]);
                    }
                    return true;
                }

                setSSFunc(this, function() {
                    var sqlArr = [ "INSERT INTO", table_info.toSql(), '('+hashKeys(object).join(', ')+')', 
                        'VALUES', '('+hashValues(object).join(', ')+')' ];
                    return sqlArr.join(" ");
                });
            },
            update  : function(args) {
                var from_node   = args[0];
                var assignments = args[1];
                var where_node  = args[2];
                this.filter  = function(dataTables, bindings) {
                    var table_info = from_node.tables[0];
                    var resultOfFromWhere = queryLang.SELECT(from_node, where_node, 1).filter(dataTables, null, {return_reference: true});
                    for (var i = 0; i < resultOfFromWhere.length; i++) {
                        var object = resultOfFromWhere[i][1];
                        for(var field in assignments) {
                            var fieldSplit = field.split('.');
                            var field_name = field;
                            if(fieldSplit.length == 2)
                                field_name = fieldSplit[1];
                            data_insertion(table_info, field_name, assignments[field], object);
                        }
                    }
                    return true;
                }

                setSSFunc(this, function() {
                    var sqlArr = [ "UPDATE", from_node.toSql() ];
                    var assignmentsArr = [];
                    for(var attr in assignments) {
                        assignmentsArr.push(attr+'='+assignments[attr])
                    }
                    sqlArr.push(assignmentsArr.join(', '));
                    if (where_node != null)
                        sqlArr.push(where_node.toSql());
                    return sqlArr.join(" ");
                });
            },
            destroy  : function(args) {
                var select_node = args[0];
                this.filter  = function(dataTables, bindings) {
                    var resultOfFromWhere = select_node.filter(dataTables, null, {return_reference: true});
                    // now go through each object, go through each attribute of it and delete it
                    for (var i = 0; i < resultOfFromWhere.length; i++) {
                        var record = resultOfFromWhere[i];
                        for(var j=1; j<record.length; j++) {
                            var object = record[j];
                            for(var attr in object) {
                                delete object[attr];
                            }
                        }
                    }
                    // then go through each table in the dataTables, each record, deleting any records that are empty objects
                    for(var table_name in dataTables) {
                        var table = dataTables[table_name]
                        for(var i = 0; i<table.length; i++) {
                            if(hashKeys(table[i]).length == 0)
                                delete table[i];
                        }
                    }
                    // then compact each table and save it back as itself
                    for(var table_name in dataTables) {
                        dataTables[table_name] = arrayCompact(dataTables[table_name]);
                    }
                    
                    return true;
                }
                
                setSSFunc(this, function() {
                    var sqlArr = [ "DELETE", select_node.toSql() ];
                    return sqlArr.join(" ").replace(/SELECT\s/, '');
                });
            },
            from    : function(tables) { this.tables = checkArgs(tables, 1, null, "FROM",   NodeType.tableDef); },
            where   : function(exprs)  { this.exprs  = checkArgs(exprs,  1, null, "WHERE",  NodeType.expression); },
            groupBy : function(exprs)  { this.exprs  = checkArgs(exprs,  1, null, "GROUP_BY"); },
            having  : function(exprs)  { this.exprs  = checkArgs(exprs,  1, null, "HAVING", NodeType.expression); },
            orderBy : function(exprs)  { this.exprs  = checkArgs(exprs,  1, null, "ORDER_BY"); },
            expression : function(args, name, opFix, sqlText, minArgs, maxArgs, jsText, alias) { 
                var theExpr    = this;
                this.args      = checkArgs(args, minArgs, maxArgs, name);
                this[".name"]  = name;
                this[".alias"] = alias != null ? alias : name;
                this.opFix     = opFix;
                this.sqlText   = sqlText != null ? sqlText : this[".name"];
                this.jsText    = jsText != null ? jsText : this.sqlText;
                this.AS = function(aliasArg) { 
                    this[".alias"] = this.ASC[".alias"] = this.DESC[".alias"] = aliasArg; 
                    return aliasReg(aliasArg, queryLang, this); 
                }
                this.ASC  = setSSFunc({ ".name": name, ".alias": theExpr[".alias"], order: "ASC" }, 
                                      function() { return theExpr[".alias"] + " ASC"; });
                this.DESC = setSSFunc({ ".name": name, ".alias": theExpr[".alias"], order: "DESC" }, 
                                      function() { return theExpr[".alias"] + " DESC"; });
                this.COLLATE = TODO;
            },
            aggregate : function() { 
                NodeType.expression.apply(this, arguments);
            },
            limit : function(offset, total) { 
                if(total == null) { // if only one parameter, it is the total
                    this.total  = cleanString(offset);
                } else {
                    this.total  = cleanString(total);
                    this.offset = cleanString(offset);
                }
            },
            tableDef : function(name, columnInfos, alias) {
                this[".name"]  = name;
                this[".alias"] = alias != null ? alias : name;
                this[".allColumns"] = [];
                for (var columnName in columnInfos) {
                    this[columnName] = new NodeType.columnDef(columnName, columnInfos[columnName], this);
                    this[".allColumns"].push(this[columnName]);
                }
                setSSFunc(this, function() { return name; });
                this.AS = function(alias) { 
                    return aliasReg(alias, queryLang, new NodeType.tableDef(name, columnInfos, alias)); 
                }
                this.ALL    = new NodeType.columnDef("*", null, this);
                this.ALL.AS = null; // SELECT T.* AS X FROM T is not legal.
            },
            columnDef : function(name, columnInfo, tableDef, alias) { // The columnInfo & tableDef might be null.
                var theColumnDef = this;
                this[".name"]  = name;
                this[".alias"] = alias != null ? alias : name;
                this.tableDef = tableDef;
                setSSFunc(this, function(flags) { 
                    if (flags != null && flags.aliasOnly == true)
                        return this[".alias"];
                    return tableDef != null ? ((tableDef[".alias"]) + "." + name) : name;
                });
                this.AS = function(aliasArg) { 
                    return aliasReg(aliasArg, queryLang, new NodeType.columnDef(name, columnInfo, tableDef, aliasArg)); 
                }
                if(columnInfo && columnInfo.type)
                    this.type = columnInfo.type
                else
                    this.type = "String";
                this.ASC  = setSSFunc({ ".name": name, ".alias": theColumnDef[".alias"], tableDef: tableDef, order: "ASC" }, 
                                      function() { return theColumnDef.toSql() + " ASC"; });
                this.DESC = setSSFunc({ ".name": name, ".alias": theColumnDef[".alias"], tableDef: tableDef, order: "DESC" }, 
                                      function() { return theColumnDef.toSql() + " DESC"; });
                this.COLLATE = TODO;
            },
            join : function(joinType, tableDef) {
                var theJoin        = this;
                this.joinType      = joinType;
                this.fromSeparator = " " + joinType + " JOIN ";
                for (var k in tableDef)
                    this[k] = tableDef[k];
                this.ON    = function() { theJoin.ON_exprs    = checkArgs(arguments, 1, null, "ON"); return theJoin; };
                this.USING = function() { theJoin.USING_exprs = cleanArray(arguments, false);        return theJoin; };
                this.fromSuffix = function() {
                    if (theJoin.ON_exprs != null)
                        return (" ON " + map(theJoin.ON_exprs, toSql).join(" AND "));
                    if (theJoin.USING_exprs != null)
                        return (" USING (" + theJoin.USING_exprs.join(", ") + ")");
                    return "";
                }
            }
        }
    
        var setSSFunc = function(obj, func) { obj.toSql = obj.toJs = obj.toString = func; return obj; };

        setSSFunc(NodeType.from.prototype, function() { 
            var sqlArr = [ "FROM " ];
            for (var i = 0; i < this.tables.length; i++) {
                if (i > 0) {
                    var sep = this.tables[i].fromSeparator;
                    if (sep == null)
                        sep = ", "
                    sqlArr.push(sep);
                }
                sqlArr.push(toSqlWithAlias(this.tables[i]));
                if (this.tables[i].fromSuffix != null)
                    sqlArr.push(this.tables[i].fromSuffix());
            }
            return sqlArr.join("");
        });

        setSSFunc(NodeType.where.prototype,   function() { return "WHERE "    + map(this.exprs,  toSql).join(" AND "); });
        setSSFunc(NodeType.orderBy.prototype, function() { return "ORDER BY " + map(this.exprs,  toSql).join(", "); });
        setSSFunc(NodeType.groupBy.prototype, function() { return "GROUP BY " + map(this.exprs,  toSql).join(", "); });
        setSSFunc(NodeType.having.prototype,  function() { return "HAVING "   + map(this.exprs,  toSql, { aliasOnly : true }).join(" AND "); });
        setSSFunc(NodeType.limit.prototype,   function() { return "LIMIT " + (this.total < 0 ? "ALL" : this.total) +
                                                                             (this.offset != null ? (" OFFSET " + this.offset) : ""); });
        
        var makeToFunc = function(toFunc, opText) {
            return function(flags) {
                if (flags != null && flags.aliasOnly == true && this[".alias"] != this[".name"])
                    return this[".alias"];
                if (this.opFix < 0) // prefix
                    return this[opText] + " (" + map(this.args, toFunc, flags).join(") " + this[opText] + " (") + ")";
                if (this.opFix > 0) // suffix
                    return "(" + map(this.args, toFunc, flags).join(") " + this[opText] + " (") + ") " + this[opText];
                return "(" + map(this.args, toFunc, flags).join(") " + this[opText] + " (") + ")"; // infix
            }
        }
    
        NodeType.expression.prototype.toSql = makeToFunc(toSql, "sqlText");
        NodeType.expression.prototype.toJs  = makeToFunc(toJs,  "jsText");

        NodeType.aggregate.prototype      = new NodeType.expression([], null, null, null, 0);
        NodeType.aggregate.prototype.toJs = function(flags) {
            if (flags != null && flags.aliasOnly == true && this[".alias"] != this[".name"])
                return this[".alias"];
            return this.jsText + " ('" + this[".alias"] + "', (" + map(this.args, toJs).join("), (") + "))";
        }

        NodeType.join.prototype = new NodeType.tableDef();

        NodeType.whereSql = function(sql) { this.exprs = [ new NodeType.rawSql(sql) ]; };
        NodeType.whereSql.prototype = new NodeType.where([new NodeType.expression([0], null, 0, null, 0, null, null, null)]);
    
        NodeType.havingSql = function(sql) { this.exprs = [ new NodeType.rawSql(sql) ]; };
        NodeType.havingSql.prototype = new NodeType.having([new NodeType.expression([0], null, 0, null, 0, null, null, null)]);

        NodeType.rawSql = function(sql) { this.sql = sql; }
        NodeType.rawSql.prototype.toSql = function(flags) { return this.sql; }
        NodeType.rawSql.prototype.toJs = function(flags) { 
            var js = this.sql;
            js = js.replace(/ AND /g, " && ");
            js = js.replace(/ OR /g, " || ");
            js = js.replace(/ = /g, " == ");
            js = js.replace(/ IS NULL/g, " == null");
            js = js.replace(/ IS NOT NULL/g, " != null");
            js = js.replace(/ NOT /g, " ! ");

            var LIKE_regex = /(\S+)\sLIKE\s'(\S+)'/g;
            var matchArr;
            while(matchArr = LIKE_regex.exec(js) ) {
                matchArr[2] = matchArr[2].replace(/%/, '.*');
                js = js.replace(LIKE_regex, "$1.match(/"+matchArr[2]+"/)");
            }

            // replace date-like strings with date object constructor
            var DATE_regex = /'(\d{4})-(\d{1,2})-(\d{1,2})'/g;
            while(matchArr = DATE_regex.exec(js) ) {
                var dateArr = [parseInt(matchArr[1], 10).toString(), (parseInt(matchArr[2], 10)-1).toString(), parseInt(matchArr[3], 10).toString()];
                var replacement = '(new Date('+dateArr.join(', ')+').valueOf())';
                js = js.replace(matchArr[0], replacement);
            }

            // NOTE: The following messes up IS NULL queries. -- steve.yen
            // >>> // replace all table+'.'+column with valueOf()
            // >>> js = js.replace(/(\w+\.\w+)/g, "$1 && $1.valueOf()");

            return js;
        }

        var keywords = {
            INSERT  :   function() { return new NodeType.insert(arguments); },
            UPDATE  :   function() { return new NodeType.update(arguments); },
            DESTROY  :   function() { return new NodeType.destroy(arguments); },
            SELECT_ALL      : function() { return new NodeType.select(arguments); },
            SELECT_DISTINCT : TODO,
            ALL   : USAGE, // We use ALL in different syntax, like SELECT_ALL.
            FROM  : function() { return new NodeType.from(arguments); },
            WHERE : function() { return new NodeType.where(arguments); },
            AND   : function() { return new NodeType.expression(arguments, "AND",  0, null, 1, null, "&&"); },
            OR    : function() { return new NodeType.expression(arguments, "OR",   0, null, 1, null, "||"); },
            NOT   : function() { return new NodeType.expression(arguments, "NOT", -1, null, 1, 1, "!"); },
            EQ    : function() { return new NodeType.expression(arguments, "EQ",   0, "=",  2, 2, "=="); },
            NEQ   : function() { return new NodeType.expression(arguments, "NEQ",  0, "!=", 2, 2); },
            LT    : function() { return new NodeType.expression(arguments, "LT",   0, "<",  2, 2); },
            GT    : function() { return new NodeType.expression(arguments, "GT",   0, ">",  2, 2); },
            LTE   : function() { return new NodeType.expression(arguments, "LTE",  0, "<=", 2, 2); },
            GTE   : function() { return new NodeType.expression(arguments, "GTE",  0, ">=", 2, 2); },
            IS_NULL     : function() { return new NodeType.expression(arguments, "IS_NULL",     1, "IS NULL",     1, 1, "== null"); },
            IS_NOT_NULL : function() { return new NodeType.expression(arguments, "IS_NOT_NULL", 1, "IS NOT NULL", 1, 1, "!= null"); },
            ADD         : function() { return new NodeType.expression(arguments, "ADD",      0, "+", 2, null); },
            SUBTRACT    : function() { return new NodeType.expression(arguments, "SUBTRACT", 0, "-", 2, null); },
            NEGATE      : function() { return new NodeType.expression(arguments, "NEGATE",  -1, "-", 1, 1); },
            MULTIPLY    : function() { return new NodeType.expression(arguments, "MULTIPLY", 0, "*", 2, null); },
            DIVIDE      : function() { return new NodeType.expression(arguments, "DIVIDE",   0, "/", 2, null); },
            PAREN       : function() { return new NodeType.expression(arguments, "PAREN",    0, "",  1, 1); },
            LIKE         : function() { return new NodeType.expression(arguments, "LIKE",   0, "LIKE",  2, 2, "match"); },
            BETWEEN      : TODO,
            AVG            : function() { return new NodeType.aggregate(arguments, "AVG",   -1, null, 1, 1); },
            AVG_ALL        : TODO,
            AVG_DISTINCT   : TODO,
            SUM            : function() { return new NodeType.aggregate(arguments, "SUM",   -1, null, 1, 1); },
            SUM_ALL        : TODO,
            SUM_DISTINCT   : TODO,
            COUNT          : function() { return new NodeType.aggregate(arguments, "COUNT", -1, null, 1, 1); },
            COUNT_ALL      : TODO,
            COUNT_DISTINCT : TODO,
            AS     : USAGE, // We use expression.AS(), table.AS(), and column.AS() instead.
            IN     : TODO,
            UNION     : TODO,
            UNION_ALL : TODO,
            EXCEPT     : TODO,
            EXCEPT_ALL : TODO,
            INTERSECT     : TODO,
            INTERSECT_ALL : TODO,
            CROSS_JOIN       : function(tableDef) { return tableDef; },
            INNER_JOIN       : function(tableDef) { return new NodeType.join("INNER", tableDef); },
            LEFT_OUTER_JOIN  : function(tableDef) { return new NodeType.join("LEFT OUTER", tableDef); },
            RIGHT_OUTER_JOIN : TODO,
            FULL_OUTER_JOIN  : TODO,
            ON               : USAGE, // We use LEFT_OUTER_JOIN(x).ON() syntax instead.
            USING            : USAGE, // We use LEFT_OUTER_JOIN(x).USING() syntax instead.
            GROUP_BY   : function() { return new NodeType.groupBy(arguments); },
            HAVING     : function() { return new NodeType.having(arguments); },
            ORDER_BY   : function() { return new NodeType.orderBy(arguments); },
            LIMIT      : function(offset, total) { return new NodeType.limit(offset, total); },
            LIMIT_ALL  : function(offset) { return queryLang.LIMIT(-1, offset); },
            OFFSET     : USAGE, // We use the shortcut comma-based syntax of "LIMIT count, offset".
            ANY_SELECT : TODO,  // TODO: Consider using syntax of LT.ANY(Invoice.total, SELECT(...))
            ALL_SELECT : TODO,
            EXISTS     : TODO,
            WHERE_SQL  : function(sql) { return new NodeType.whereSql(sql); },
            HAVING_SQL : function(sql) { return new NodeType.havingSql(sql); }
        };
        
        keywords.SELECT = keywords.SELECT_ALL;
    
        for (var k in keywords)
            queryLang[k] = keywords[k];
        for (var tableName in tableInfos)
            queryLang[tableName] = new NodeType.tableDef(tableName, tableInfos[tableName]);
        return queryLang;
    }

    /////////////////////////////////////////////////////
    
    var compileJoinDriver = function(tables) { // The join driver naively visits the cross-product.
        var funcText = [ "var TrimPath_query_tmpJD = function(dataTables, joinFilter, whereFilter, bindings) {",
                         "var result = [], filterArgs = [ bindings ];" ];
        for (var i = 0; i < tables.length; i++)
            funcText.push("var T" + i + " = dataTables['" + tables[i][".name"] + "'] || [];");
        for (var i = 0; i < tables.length; i++) {
            funcText.push("for (var t"+i+" = 0; t"+i+" < T"+i+".length; t"+i+"++) {");
            funcText.push("var resultLength"+i+" = result.length;");
            funcText.push("filterArgs["+(i+1)+"] = T"+i+"[t"+i+"];");
        }
        funcText.push("if ((joinFilter == null || joinFilter.apply(null, filterArgs) == true) && ");
        funcText.push("    (whereFilter == null || whereFilter.apply(null, filterArgs) == true))");
        funcText.push(    "result.push(filterArgs.slice(0));");
        for (var i = tables.length - 1; i >= 0; i--) {
            funcText.push("}");
            if (i >= 1 && tables[i].joinType == "LEFT OUTER") {
                funcText.push("if (resultLength"+(i-1)+" == result.length) {");
                for (var j = i; j < tables.length; j++)
                    funcText.push("filterArgs[" + (j+1) + "] = ");
                funcText.push("{}; if (whereFilter == null || whereFilter.apply(null, filterArgs) == true) result.push(filterArgs.slice(0)); }");
            }
        }
        funcText.push("return result; }; TrimPath_query_tmpJD");
        return theEval(funcText.join(""));
    }

    var compileFilter = function(bodyFunc, tables, whereExpressions, flags) { // Used for WHERE and HAVING.
        var funcText = [ "var TrimPath_query_tmpWF = function(_BINDINGS" ];
        for (var i = 0; i < tables.length; i++)
            funcText.push(", " + tables[i][".alias"]);
        funcText.push("){ with(_BINDINGS) {");
        bodyFunc(funcText, tables, whereExpressions, flags);
        funcText.push("return true; }}; TrimPath_query_tmpWF");
        return theEval(funcText.join(""));
    }
    
    var compileFilterForJoin = function(funcText, tables, whereExpressions, flags) {
        for (var i = 0; i < tables.length; i++) { // Emit JOIN ON/USING clauses.
            if (tables[i].joinType != null) {
                if (tables[i].ON_exprs != null || tables[i].USING_exprs != null) {
                    funcText.push("if (!(");
                    if (tables[i].ON_exprs != null && tables[i].ON_exprs[0].exprs != null) {
                        funcText.push(tables[i].ON_exprs[0].exprs[0].toJs())
                    } else if(tables[i].ON_exprs != null)
                        funcText.push(map(tables[i].ON_exprs, toJs).join(" && "));
                    if (tables[i].USING_exprs != null)
                        funcText.push(map(tables[i].USING_exprs, function(col) {
                                return "(" + tables[i - 1][".alias"] + "." + col + " == " + tables[i][".alias"] + "." + col + ")";
                            }).join(" && "));
                    funcText.push(")) return false;");
                }
            }
        }
    }

    var compileFilterForWhere = function(funcText, tables, whereExpressions, flags) {
        if (whereExpressions != null) {
            funcText.push("if (!(("); // Emit the main WHERE clause test.
            for (var i = 0; i < whereExpressions.length; i++) {
                if (i > 0)
                    funcText.push(") && (");
                funcText.push(toJs(whereExpressions[i], flags));
            }
            funcText.push("))) return false;");
        }
    }
    var compileColumnConvertor = function(tables, columnExpressions) {
        var funcText = [ "var TrimPath_query_tmpCC = function(_BINDINGS, " ];
        var table_aliases = [];
        for (var i = 0; i < tables.length; i++)
            table_aliases.push(tables[i][".alias"]);
        funcText.push(arrayUniq(table_aliases).join(', '));
        funcText.push(", with_table){ with(_BINDINGS) {");
        funcText.push("var _RESULT = {};");
        funcText.push("if(with_table) {");
        compileColumnConvertorHelper(funcText, columnExpressions, true);
        funcText.push("} else {");
        compileColumnConvertorHelper(funcText, columnExpressions, false);
        funcText.push("}");
        funcText.push("return _RESULT; }}; TrimPath_query_tmpCC");
        return theEval(funcText.join(""));
    }

    var test = function(stuff) {
        var i;
    }
    var compileColumnConvertorHelper = function(funcText, columnExpressions, with_table) {
        for (var i = 0; i < columnExpressions.length; i++) {
            var columnExpression = columnExpressions[i];
            if (columnExpression[".name"] == "*") {
                compileColumnConvertorHelper(funcText, columnExpression.tableDef[".allColumns"], with_table);
            } else {
                funcText.push("_RESULT['"); // TODO: Should we add _RESULT[i] as assignee?
                if(with_table == true) {
                    funcText.push(columnExpression.toString());
                } else {
                    funcText.push(columnExpression[".alias"]);
                }
                funcText.push("'] = (");
                funcText.push(toJs(columnExpression));
                funcText.push(");");
            }
        }
    }
    
    var dateToString = function(date) {
        if(typeof date == 'object')
            return [date.getFullYear(), '-', (date.getMonth()+1), '-', date.getDate()].join('');
        if(date == null)
            return null;
    }

    var compileOrderByComparator = function(orderByExpressions) {
        var funcText = [ "var TrimPath_query_tmpOC = function(A, B) { var a, b; " ];
        for (var i = 0; i < orderByExpressions.length; i++) {
            var orderByExpression = orderByExpressions[i];
            if(orderByExpression.tableDef) {
                funcText.push("a = A['" + orderByExpression[".alias"] + "'] || A['" + 
                    orderByExpression.tableDef['.alias'] + '.' + orderByExpression[".alias"] + "'] || '';");
                funcText.push("b = B['" + orderByExpression[".alias"] + "'] || B['" + 
                    orderByExpression.tableDef['.alias'] + '.' + orderByExpression[".alias"] + "'] || '';");
            } else {
                funcText.push("a = A['" + orderByExpression[".alias"] + "'] || '';");
                funcText.push("b = B['" + orderByExpression[".alias"] + "'] || '';");
            }
            var sign = (orderByExpression.order == "DESC" ? -1 : 1);
            funcText.push("if (a.valueOf() < b.valueOf()) return " + (sign * -1) + ";");
            funcText.push("if (a.valueOf() > b.valueOf()) return " + (sign * 1) + ";");
        }
        funcText.push("return 0; }; TrimPath_query_tmpOC");
        return theEval(funcText.join(""));
    }

    var compileGroupByCalcValues = function(tables, groupByExpressions) {
        var funcText = [ "var TrimPath_query_tmpGC = function(_BINDINGS" ];
        for (var i = 0; i < tables.length; i++)
            funcText.push(", " + tables[i][".alias"]);
        funcText.push("){ var _RESULT = [];");
        for (var i = 0; i < groupByExpressions.length; i++) {
            funcText.push("_RESULT.push(");
            funcText.push(toJs(groupByExpressions[i]));
            funcText.push(");");
        }
        funcText.push("return _RESULT; }; TrimPath_query_tmpGC");
        return theEval(funcText.join(""));
    }

    /////////////////////////////////////////////////////

    var groupByComparator = function(a, b) {
        return arrayCompare(a.groupByValues, b.groupByValues);
    }

    var arrayCompare = function(x, y) {
        if (x == null || y == null) return -1; // Required behavior on null for GROUP_BY to work.
        for (var i = 0; i < x.length && i < y.length; i++) {
            if (x[i] < y[i]) return -1;
            if (x[i] > y[i]) return 1;
        }
        return 0;
    }
    
    var toSqlWithAlias = function(obj, flags) { 
        var res = toSql(obj, flags);
        if (obj[".alias"] != null && 
            obj[".alias"] != obj[".name"])
            return res + " AS " + obj[".alias"];
        return res;
    }
    var toSql = function(obj, flags) { return toX(obj, "toSql", flags); }
    var toJs  = function(obj, flags) { return toX(obj, "toJs",  flags); }
    var toX   = function(obj, funcName, flags) {
        if (typeof(obj) == "object" && obj[funcName] != null)
            return obj[funcName].call(obj, flags);
        return theString(obj);
    }

    var zeroDefault = function(x) { return (x != null ? x : 0); }
    
    var map = function(arr, func, arg2) { // Lisp-style map function on an Array.
        for (var result = [], i = 0; i < arr.length; i++)
            result.push(func(arr[i], arg2));
        return result;
    }

    var cleanArray = function(src, quotes) {
        for (var result = [], i = 0; i < src.length; i++)
            result.push(cleanString(src[i], quotes));
        return result;
    }

    var cleanString = TrimPath.TEST.cleanString = function(src, quotes) { // Example: "hello" becomes "'hello'"
        if (src instanceof theString || typeof(src) == "string") {
            src = theString(src).replace(/\\/g, '\\\\').replace(/'/g, "\\'");
            if (quotes != false) // Handles null as true.
                src = "'" + src + "'";
        }
        return src;
    }

    var findClause = function(str, regexp) {
        var clauseEnd = str.search(regexp);
        if (clauseEnd < 0)
            clauseEnd = str.length;
        return str.substring(0, clauseEnd);
    }

    QueryLang.prototype.parseSQL = function(sqlQueryIn, paramsArr) { // From sql to tql.
        var sqlQuery = sqlQueryIn.replace(/\n/g, ' ').replace(/\r/g, '');
        
        if (paramsArr != null) { // Convert " ?" to args from optional paramsArr.
            if (paramsArr instanceof theArray == false)
                paramsArr = [ paramsArr ];

            var sqlParts = sqlQuery.split(' ?');
            for (var i = 0; i < sqlParts.length - 1; i++)
                sqlParts[i] = sqlParts[i] + ' ' + cleanString(paramsArr[i], true);
            sqlQuery = sqlParts.join('');
        }

        sqlQuery = sqlQuery.replace(/ AS ([_a-zA-z0-9]+)/g, ".AS('$1')");

        var err = function(errMsg) { 
            throw ("[ERROR: " + errMsg + " in query: " + sqlQueryIn + "]"); 
        };
        
        var query_type = sqlQuery.split(/\s+/)[0];
        if (query_type == 'DELETE')
            query_type = 'DESTROY';
            
        if (!arrayInclude(['SELECT', 'DESTROY', 'UPDATE', 'INSERT'], query_type))
            err("not a valid query type");
        
        var strip_whitespace = function(str) {
            return str.replace(/\s+/g, '');
        }
        
        if (query_type == 'SELECT' || query_type == 'DESTROY') {
            
            var fromSplit = sqlQuery.substring(7).split(" FROM ");
            if (fromSplit.length != 2)
                err("missing a FROM clause");
            
            //SELECT Invoice.*, Customer.* FROM Invoice, Customer
            //SELECT * FROM Invoice, Customer
            //DELETE things, relationships FROM relationships LEFT OUTER JOIN things ON things.relationship_id = relationships.id WHERE relationships.id = 2
            //SELECT * FROM relationships LEFT OUTER JOIN users ON relationships.created_by = users.id AND relationships.updated_by = users.id LEFT OUTER JOIN things ON things.relatedrelationship_id = relationships.id  ORDER BY relationships.updated_at DESC LIMIT 0, 20
            var columnsClause = fromSplit[0].replace(/\.\*/g, ".ALL");
            var remaining     = fromSplit[1];
            var fromClause    = findClause(remaining, /\sWHERE\s|\sGROUP BY\s|\sHAVING\s|\sORDER BY\s|\sLIMIT/);
            var fromTableClause = findClause(fromClause, /\sLEFT OUTER JOIN\s/);
            var fromTables = strip_whitespace(fromTableClause).split(',');
            remaining = remaining.substring(fromClause.length);
            
            var fromClauseSplit = fromClause.split(" LEFT OUTER JOIN ");
            var fromClauseParts = [fromClauseSplit[0]];
            var leftJoinComponents;
            for (var i = 1; i < fromClauseSplit.length; i++) {
                leftJoinComponents = /(\w+)\sON\s(.+)/.exec(fromClauseSplit[i]);
                fromTables.push(leftJoinComponents[1]);
                fromClauseParts.push( '('+leftJoinComponents[1]+')'+'.ON(WHERE_SQL("'+leftJoinComponents[2]+'"))' );
            }
            fromClause = fromClauseParts.join(", LEFT_OUTER_JOIN");
            
            if(strip_whitespace(columnsClause) == '*') {
                var new_columns = [];
                for(var i=0; i<fromTables.length; i++) {
                    new_columns.push(fromTables[i]+'.ALL')
                }
                columnsClause = columnsClause.replace(/\*/, new_columns.join(', '))
            }
            var whereClause   = findClause(remaining, /\sGROUP BY\s|\sHAVING\s|\sORDER BY\s|\sLIMIT/);
            remaining = remaining.substring(whereClause.length);
            var groupByClause = findClause(remaining, /\sHAVING\s|\sORDER BY\s|\sLIMIT /);
            remaining = remaining.substring(groupByClause.length);
            var havingClause  = findClause(remaining, /\sORDER BY\s|\sLIMIT /);
            remaining = remaining.substring(havingClause.length);
            var orderByClause = findClause(remaining, /\sLIMIT /).replace(/\sASC/g, ".ASC").replace(/\sDESC/g, ".DESC");
            remaining = remaining.substring(orderByClause.length);
            var limitClause   = remaining;
            
            var tql = [ 'SELECT(FROM(', fromClause, '), ', columnsClause];
            if (whereClause.length > 0)
                tql.push(', WHERE_SQL("' + whereClause.substring(7) + '")');
            if (groupByClause.length > 0)
                tql.push(', GROUP_BY(' + groupByClause.substring(10) + ')');
            if (havingClause.length > 0)
                tql.push(', HAVING_SQL("' + havingClause.substring(8) + '")');
            if (orderByClause.length > 0)
                tql.push(', ORDER_BY(' + orderByClause.substring(10) + ')');
            if (limitClause.length > 0)
                tql.push(', LIMIT(' + limitClause.substring(7) + ')');
            tql.push(')');
        }
        else if (query_type == "INSERT") {
            // accepts sql of the format: INSERT INTO things (field1, field2) VALUES ('value1', 'value2')
            var intoSplit = sqlQuery.substring(6).split(" INTO ");
            if (intoSplit.length != 2)
                err("missing an INTO clause");
            var insertion_regex = /^\s*(\w+)\s*\((.+)\)\s+VALUES\s+\((.+)\)/
            var parsed_sql = intoSplit[1].match(insertion_regex);
            var table_name = parsed_sql[1];
            var fields = strip_whitespace(parsed_sql[2]).split(',');
            var values = parsed_sql[3].split(',');
            if (fields.length != values.length)
                err("values and fields must have same number of elements");
            
            tql = ['INSERT(', table_name, ',', simpleJson(fields, values), ')'];
        }
        else if (query_type == "UPDATE") {
            // UPDATE things SET relatedrelationship_id=2, name="poop" WHERE things.relatedrelationship_id=1
            //var tql = ['UPDATE(FROM(things ), {"relatedrelationship_id": "2"}, WHERE_SQL("things.relatedrelationship_id = 1"))'];
            var setSplit = sqlQuery.substring(7).split(" SET ");
            if (setSplit.length != 2)
                err("missing a SET clause");
            var fromClause = setSplit[0];
            var remaining  = setSplit[1];
            var assignmentClause   = findClause(remaining, /\sWHERE\s/);
            remaining = remaining.substring(assignmentClause.length);
            var whereClause = remaining;
            var assignmentArray = assignmentClause.split(',');
            var fields = [];
            var values = [];
            for (var i=0; i<assignmentArray.length; i++) {
                var components = assignmentArray[i].split('=');
                fields.push(strip(components[0]));
                values.push(strip(components[1]));
            }
            var update_regex = /^UPDATE\s+(\w+)\s+SET\s+(\w+\s*=\s*\w+)/
            var parsed_sql = sqlQuery.match(update_regex);
            
            var tql = ['UPDATE(FROM(', fromClause, '), ', simpleJson(fields, values)];
            tql.push(', WHERE_SQL("' + whereClause.substring(7) + '")');
            tql.push(')');
        }
        if(query_type == 'DESTROY') {
            tql.unshift('DESTROY(');
            tql.push(')');
        }
        with (this) {
            return eval(tql.join(''));
        }
    }
}) ();
