window.debug = false
window.default_hostname = window.location.hostname
window.web_resource_base = "http://" + window.default_hostname + ":8000/"
window.jsonrpc_id = 0
window.wrong_command_format_str = "Invalid command format"
window.sentinel_value = "" 
window.syntax_error_value = -1
function alert_if_debug(alert_str) {
    if(window.debug) {
	alert("DEBUG: " + alert_str)
    }
}

function was_successful_call(returnedData) {
    return 'result' in returnedData
}

function handle_error(error, term) {
    error_str = "error message: " + error['message']
    term.echo(error_str)
    console.log(error)
}

function parse_infer_result(infer_return) {
    ret_str = ""
    for(var i=0; i<infer_return.length; i++) {
	infer_return_i = infer_return[i]
	coordinates = String([infer_return_i[0], infer_return_i[1]])
	value = String(infer_return_i[2])
	ret_str += coordinates + ": " + value + "\n"
    }
    return ret_str
}

function echo_if_debug(echo_str, term) {
    if(window.debug) {
	term.echo("DEBUG: " + echo_str)
    }
}

function if_undefined(variable, default_value) {
    if(typeof(variable)=="undefined") {
	variable = default_value
    }
    return variable
}

function nan_to_blank(el) {
    return String(el).toUpperCase()=="NAN" ? "" : el
}   

function map_nan_to_blank(data) {
    row_mapper = function(row) { return row.map(nan_to_blank) }
    return data.map(row_mapper)
}

function convert_column_str_list(columns) {
    columns_out = []
    for(column_idx in columns) {
	column_dict = {"sClass": "center", "sTitle": columns[column_idx]}
	columns_out.push(column_dict)
    }
    return columns_out
}

function load_to_datatable(data, columns, sorting) {
    $('#dynamic').html( '<table cellpadding="0" cellspacing="0" border="0" class="display" id="example"></table>' );
    data = if_undefined(data, [])
    data = map_nan_to_blank(data)
    columns = if_undefined(columns, [])
    sorting = if_undefined(sorting, [])
    $('#example').dataTable( {
	"aaData": data,
	"aoColumns": columns,
	"aaSorting": sorting,
	"aLengthMenu": [100, 200, 1000],
	"iDisplayLength": 100
    } );
}

/* Converter functions*/
function encodeValues(observedValue){
    return observedValue
}

function missingValuesQuerisToJSON(missingValueIndices){
    q = missingValueIndices
    return {"q":q}
}

function findNaNValuesInCSV(csvFile){
    var arrayDataSet = $.csv.toArrays(csvFile);
    var numCols = arrayDataSet[0].length - 1 
    var numRows = arrayDataSet.length - 1
    var missingValsList = []
    for (var i = 1; i < numRows + 1; i++){
	for (var j = 0; j < numCols; j++){
	    if (arrayDataSet[i][j] == "NaN"){
		missingValsList.push([i -1 , j - 1])
	    }
	    
	}
    }
    return missingValsList
}

function set_menu_option(option_value) {
    jQuery(document.getElementById('menu')).append(
	"<option value='" + option_value + "'>" + 
	    option_value + "</option>"
    )
}

function JSONRPC_send_method(method_name, parameters, function_to_call) {
    window.jsonrpc_id += 1
    data_in =
	{ id : toString(window.jsonrpc_id),
	  jsonrpc : "2.0",
	  method : method_name,
	  params : parameters }
    $.ajax({
	url: window.JSONRPC_URL, 
	type: 'PUT', 
	data: JSON.stringify(data_in),
	dataType: 'json', 
	async: true,	
	crossDomain: true,
	success:function(data) {
	    function_to_call(data)
	},
	error: function(httpRequest, textStatus, errorThrown) {
	    console.log(httpRequest)
	    console.log(textStatus)
	    console.log(errorThrown)
	    alert("Sorry, some error has happened.")
	},
	complete: function() {
	    //console.log('COMPLETE');
	}		
    });			    
}

function to_upper_case(str) {
    return str.toUpperCase()
}

function get_idx_of(term, str_array) {
    return $.inArray(term.toUpperCase(), str_array.map(to_upper_case))
}

function in_list(term, str_array) {
    return get_idx_of(term, str_array) != -1
}

function get_idx_after(term, str_array) {
    return get_idx_of(term, str_array) + 1
}

function get_el_after(term, str_array) {
    // case insensitive
    idx = get_idx_after(term, str_array)
    return str_array[idx]
}

/* Parser functions*/
function parseCreateTableCommand(commandString){
    var columnsDict = new Object()
    command_split = commandString.split(' ')
    if (!in_list("FROM", command_split)){ // check if we have the right syntax
    	return window.syntax_error_value
    }
    // extract column names
    columnNamesIndex =  get_idx_after("WITH", command_split)
    var i = columnNamesIndex
    while (i < command_split.length && i != 0){
	// FIXME: should verify command_split[i+1] is 'AS'
    	if (command_split[i+1] != "AS"){
    	    return window.syntax_error_value //wrong syntax 
    	}
    	columnsDict[command_split[i]] = command_split[i+2]
    	i += 3
    }
    //
    var tableName;
    tableName = get_el_after("PTABLE", command_split)
    fileName = get_el_after("FROM", command_split)
    //
    var returnDict = new Object()
    returnDict["tableName"] = tableName
    returnDict["fileName"] = fileName
    returnDict["columns"] = columnsDict
    return returnDict
}



function parseCreateModelCommand(commandString){
    command_split = commandString.split(' ')
    var returnDict = new Object()
    if (!in_list("FOR", command_split)){ // check if we have the right syntax
    	return window.syntax_error_value
    }
    tableName = get_el_after("FOR", command_split)
    numberOfChains = 10 //default value
    if(in_list("WITH", command_split)) {
	numberOfChains = get_el_after("WITH", command_split)
    }	
    returnDict["tableName"] = tableName
    returnDict["numberOfChains"] = parseInt(numberOfChains)
    return returnDict
}



function parseAnalyzeCommand(commandString){
    command_split = commandString.split(' ');
    var returnDict = new Object()
    tableName = get_el_after("ANALYZE", command_split)
    iterations = 2 //default value
    if(in_list("FOR", command_split)) {
	iterations = get_el_after("FOR", command_split)
	iterations = parseInt(iterations)
    }
    which_chain = 'ALL' //default value
    if(in_list("ON", command_split)) {
	which_chain_idx = get_idx_after("ON", command_split)
	which_chain = command_split[which_chain_idx]
	which_chain = parseInt(which_chain)
    }
    returnDict["tableName"] = tableName
    returnDict["iterations"] = iterations
    returnDict["chainIndex"] = which_chain
    return returnDict
}


function parseDropCommand(commandString){
    command_split = commandString.split(' ');
    var returnDict = new Object()
    tableName = get_el_after("PTABLE", command_split)
    returnDict["tableName"] = tableName
    return returnDict
}


function parseDeleteChainCommand(commandString){
    command_split = commandString.split(' ');
    if (!in_list("FOR", command_split)){ // check if we have the right syntax
    	return window.syntax_error_value
    }
    var returnDict = new Object()
    tableName = get_el_after("FOR", command_split) 
    chain_idx = get_el_after("CHAIN", command_split)  
    returnDict["tableName"] = tableName
    returnDict["chainIndex"] = parseInt(chain_idx)
    return returnDict
}



function findColumnsType(csvDataFile){
    //TODO this is going to be done in the middleware, the user will either specify the types or trust the middleware's guess
    var aDataSet = $.csv.toArrays(csvDataFile); 
    var colTypeDict = new Object();
    var counter = 0;
    for (var c = 0 ; c < aDataSet[0].length ; c++){
	colTypeDict[aDataSet[0][c]] = "continuous"
	counter += 1
    }
    colTypeDict["NAME"] = "ignore"
    return colTypeDict
}

function typeDictToTable(typeDict){
    var aDataSetKeys = Object.keys(typeDict)
    var columns = new Array();
    var counter = 0;
    for (var c in aDataSetKeys){
	columns[counter] = { "sTitle": aDataSetKeys[counter] , "sClass": "center"}
	counter += 1
    }
    
    var out = "";
    for (var r = 0; r < aDataSetKeys.length - 1; r++) {
	out += typeDict[aDataSetKeys[r]] + ", ";
    }
    out += typeDict[aDataSetKeys[aDataSetKeys.length]]
    load_to_datatable([], columns, sorting)
}

function parseInferCommand(commandString){
    // INFER col0, [col1,...] [INTO into_table] FROM [from_table]
    // WHERE whereclause WITH CONFIDENCE confidence_level [LIMIT limit] [NUMSAMPLES numsamples]
    var returnDict = new Object() 
    command_split = commandString.split(' ');
    missing_from = !in_list("FROM", command_split)
    missing_with = !in_list("WITH", command_split)
    missing_confidence = !in_list("CONFIDENCE", command_split)
    if (missing_confidence || missing_from || missing_with) { 
    	return window.syntax_error_value
    }

    // these arguments are optional
    newtablename = window.sentinel_value
    whereclause = window.sentinel_value
    limit = 100
    numsamples = 100

    // get columns
    start_idx = get_idx_after("INFER", command_split)
    if (in_list("INTO", command_split)){
	end_idx = get_idx_of("INTO", command_split)
    } else {
	end_idx = get_idx_of("FROM", command_split)
    }
    columnsToSelectFrom = command_split.slice(start_idx, end_idx) 
    columnsString = columnsToSelectFrom.join("")
    //
    if (in_list("INTO", command_split)) {
	newtablename = get_el_after("INTO", command_split) 
    }
    //
    tableName = get_el_after("FROM", command_split) 
    //
    if (in_list("WHERE", command_split)){
	start_idx = get_idx_after("WHERE", command_split)
	end_idx = get_idx_of("WITH", command_split)
	whereClause = command_split.slice(start_idx, end_idx)
	var whereclause = whereClause.join().replace( /,/g, " " )
    }
    confidence = get_el_after("CONFIDENCE", command_split)  
    //
    if (in_list("LIMIT", command_split)){
    	limit = get_el_after("LIMIT", command_split) 
    }
    //
    if (in_list("NUMSAMPLES", command_split)){
    	numsamples = get_el_after("NUMSAMPLES", command_split) 
    }

    returnDict["tablename"] = tableName
    returnDict["columnstring"] = columnsString
    returnDict["newtablename"] = newtablename
    returnDict["confidence"] = parseFloat(confidence)
    returnDict["whereclause"] =  whereclause
    returnDict["limit"] = parseInt(limit)
    returnDict['numsamples'] = parseInt(numsamples)
    
    console.log(returnDict)
    return returnDict
}

function parsePredictCommand(commandString){
    // PREDICT col0, [col1, ...] FROM tablename WHERE conditions TIMES times
    var returnDict = new Object() 
    command_split = commandString.split(' ');
    missing_from = !in_list("FROM", command_split)
    missing_times = !in_list("TIMES", command_split)
    if (missing_from || missing_times) {
    	return window.syntax_error_value
    }
    // FIXME: is WHERE optional?
    whereclause = window.sentinel_value
    if (in_list("WHERE", command_split)){
	start_idx = get_idx_after("WHERE", command_split)
	end_idx = get_idx_of("WITH", command_split)
	whereClause = command_split.slice(start_idx, end_idx)
	var whereclause = whereClause.join().replace( /,/g, " " )
    }

    start_idx = get_idx_after("PREDICT", command_split)
    end_idx = get_idx_of("FROM", command_split)
    columnsToSelectFrom = command_split.slice(start_idx, end_idx)
    columnsstring = columnsToSelectFrom.join('')
    //
    tablename = get_el_after("FROM", command_split)  
    //
    // FIXME: consider 'FOR' instead of 'TIMES'
    //        then it makes sense for the number to come after
    start_idx = get_idx_after("WHERE", command_split)
    end_idx = get_idx_of("TIMES", command_split)
    whereclause = command_split.slice(start_idx, end_idx).join(' ')
    //
    times = parseInt(get_el_after("TIMES", command_split))
    // FIXME: take as an argument
    newtablename = tablename + '_predict'
    returnDict["columnstring"] = columnsstring
    returnDict["newtablename"] = newtablename
    returnDict["tablename"] = tablename
    returnDict["whereclause"] =  whereclause
    returnDict["numpredictions"] = times
    
    console.log(returnDict)
    return returnDict
}

/* Loading and jqueries functions*/
function LoadToDatabaseTheCSVData(fileName, highlight_maybe_set) {
    data = preloadedDataFiles[fileName]
    window.masterData = data
    window.currentTable = fileName;
    
    var aDataSet = $.csv.toArrays(data); 
    var columns = new Array();
    var counter = 0;
    for (var c in aDataSet[0]){
	columns[counter] = { "sTitle": aDataSet[0][c] , "sClass": "center"}
	counter += 1
    }
    aDataSet.shift()  
    load_to_datatable(aDataSet, columns, [])
    if (highlight_maybe_set.length != 0){
	example_element = document.getElementById("example")
	for (var i = 0; i < highlight_maybe_set.length ; i ++){
	    // add 1 to row for column names
	    row_idx = highlight_maybe_set[i][0] + 1
	    col_idx = highlight_maybe_set[i][1]
	    cell_element = example_element.rows[row_idx].cells[col_idx]
	    jQuery(cell_element).addClass("redText")
	    if(typeof(highlight_maybe_set[i][2])!="undefined") {
		value = highlight_maybe_set[i][2]
		jQuery(cell_element).html(value)
	    }
	}
    }
}

function write_json_for_table(tablename) {
    empty_callback = function(returnedData) {}
    JSONRPC_send_method("write_json_for_table", {"tablename":tablename}, empty_callback)
}

$(document).ready(function() {	 
    window.commandHistory = [];
    window.scrollChange = false
    window.currentTable = "";
    layout_dict = {
	north:{size:0.4},
	west:{initHidden:true},
	east:{size:0.5}
    }
    $('body').layout(layout_dict)
    window.sliders.style.display = 'none';
} );  



jQuery(function($, undefined) {
    $('#term_demo').terminal(function(command, term) {
	command_split = command.split(' ')
	first_command_uc = command_split[0].toUpperCase()
	if (command !== ''){
	    commandHistory.push(command)
	}
	if (command !== '' || commandHistory.length != 0) {
	    try {
		switch (first_command_uc)
		{
		case "PING": {
		    function_to_call = function(returnedData) {
			if(was_successful_call(returnedData)) {
			    term.echo("GOT TO SERVER")		    
			} else {
			    term.echo("CAN'T FIND SERVER AT: " + window.JSONRPC_URL)
			}
			console.log(returnedData)
		    }
		    JSONRPC_send_method("ping", {}, function_to_call)
		    break
		}
		case "SETHOSTNAME":
		    {
			hostname = command_split[1]
			set_url_with_hostname(hostname)
			echo_if_debug("JSONRPC_URL = " + window.JSONRPC_URL, term)
			break
		    }
		case "GETHOSTNAME":
		    {
			term.echo("JSONRPC_URL = " + window.JSONRPC_URL)
			break
		    }
		case "START": {
		    command_split[1] = if_undefined(command_split[1], '')
		    command_split[2] = if_undefined(command_split[2], '')
		    has_from = command_split[1].toUpperCase() == 'FROM'
		    has_scratch = command_split[2].toUpperCase() == 'SCRATCH'
		    if(has_from && has_scratch) {
			dict_to_send = {}
			callback_func = function(returnedData) {
			    if(was_successful_call(returnedData)) {
				term.echo("STARTED DATABASE FROM SCRATCH")
			    } else {
				term.echo("FAILED TO START FROM SCRATCH")
				handle_error(returnedData['error'], term)
			    }
			}
			JSONRPC_send_method("start_from_scratch", {}, callback_func)
		    } else {
	    		term.echo(window.wrong_command_format_str);
			term.echo("Did you mean 'START FROM SCRATCH'?")
		    }
		    break
			
		}
		case "DUMP": {
		    filename = command_split[1]
		    if(typeof(filename)=='undefined') {
	    		term.echo(window.wrong_command_format_str);
			term.echo("Did you mean 'DUMP <FILENAME>'?")
			break
		    }
		    linkname = window.web_resource_base + filename
		    success_str = ("DUMPED DATABASE: " + linkname)
		    fail_str = ("FAILED TO DUMP DATABASE")
		    dict_to_send = {
			"filename":filename
		    }
		    callback_func = function(returnedData) {
			console.log(returnedData)
			if(was_successful_call(returnedData)) {
			    term.echo(success_str)
			} else {
			    term.echo(fail_str)
			    handle_error(returnedData['error'], term)
			}
		    }
		    JSONRPC_send_method("dump_db", dict_to_send, callback_func)
		    break
		}
		case "DROPANDLOAD": {
		    filename = command_split[1]
		    dict_to_send = {"filename":filename}
		    success_str = ('DROPPED DB AND LOADED FROM FILENAME: '
				   + filename)
		    fail_str = ('FAILED TO DROP DB AND LOAD')
		    callback_func = function(returnedData) {
			console.log(returnedData)
			if(was_successful_call(returnedData)) {
			    term.echo(success_str)
			} else {
			    term.echo(fail_str)
			    handle_error(returnedData['error'], term)
			}
		    }
		    JSONRPC_send_method("drop_and_load_db", dict_to_send,
					callback_func)
		    break
		}
		case "SHOW": {
		    command_split[1] = if_undefined(command_split[1], '')
		    command_split[2] = if_undefined(command_split[2], '')
		    command_split[3] = if_undefined(command_split[3], '')
		    if(command_split[1].toUpperCase()=='COLUMN'
		       && command_split[2].toUpperCase()=='DEPENDENCIES'
		       && command_split[3].toUpperCase()=='FOR') {
			tablename = command_split[4]
			filename = tablename + '_feature_z.png'
			success_str = ("SHOWING COLUMN DEPENDENCIES FOR "
				       + tablename)
			fail_str = ("FAILED TO GENERATE COLUMN DEPENDENCIES")
			dict_to_send = {
			    "tablename":tablename,
			    "filename":filename,
			}
			callback_func = function(returnedData) {
			    console.log(returnedData)
			    if(was_successful_call(returnedData)) {
				set_kitware(filename)
				term.echo(success_str)
			    } else {
				term.echo(fail_str)
				handle_error(returnedData['error'], term)
			    }
			}
			JSONRPC_send_method("gen_feature_z", dict_to_send,
					    callback_func)
		    } else {
	    		term.echo(window.wrong_command_format_str);
			term.echo("Did you mean 'SHOW COLUMN DEPENDENCIES FOR <PTABLE>?'")
		    }
		    break
		}
		case "CREATE": 
		    {
	    		if (command_split[1].toUpperCase() == "PTABLE")
	    		{ 
	    		    echo_if_debug("CREATE PTABLE", term)
			    tempString = parseCreateTableCommand(command)
			    if (tempString == window.syntax_error_value){
			    	term.echo(window.wrong_command_format_str);
			    	break
			    }
			    console.log(tempString)
			    filename = tempString["fileName"]
			    tablename = tempString["tableName"]
			    crosscat_column_types = tempString["columns"]
			    if(typeof(crosscat_column_types)=="undefined") {
				crosscat_column_types = "NONE"
			    }
			    dict_to_send = {
				"csv": preloadedDataFiles[filename],
				"crosscat_column_types": crosscat_column_types,
				"tablename": tablename,
			    }
			    success_str = ("CREATED PTABLE " + tablename)
			    fail_str = ("FAILED TO CREATE PTABLE " + tablename)
			    callback_func = function(returnedData) {
				console.log(returnedData)
				if(was_successful_call(returnedData)) {
				    term.echo(success_str)
				} else {
				    term.echo(fail_str)
				    handle_error(returnedData['error'], term)
				}
			    }
			    JSONRPC_send_method("upload_data_table", dict_to_send, callback_func)
			    //in case the table name is different than the file name
			    if (tempString["fileName"] != tempString["tableName"]){
			    	var temp = preloadedDataFiles[tempString["fileName"]]
			    	preloadedDataFiles[tempString["tableName"]] = temp
			    	delete preloadedDataFiles[tempString["fileName"]]
			    	var select=document.getElementById('menu');
			    	for (i=0;i<select.length;  i++) {
			    	    if (select.options[i].value==tempString["fileName"]) {
			    		select.remove(i);
			    	    }
			    	}
				set_menu_option(tempString['tableName'])
			    }
			}
	    		
	    		else if (command_split[1].toUpperCase() == "MODEL")
	    		{ 
	    		    echo_if_debug("CREATE MODEL", term)
			    tempString = parseCreateModelCommand(command)
			    if (tempString == window.syntax_error_value){
			    	term.echo(window.wrong_command_format_str);
			    	break
			    }
			    tablename = tempString["tableName"]
			    n_chains = tempString["numberOfChains"]
			    dict_to_send = {
				"tablename": tablename,
				"n_chains": n_chains,
			    }
			    success_str = ("CREATED MODEL FOR " + tablename
					   + " WITH " + n_chains
					   + " EXPLANATIONS")
			    fail_str = "FAILED TO CREATE MODEL FOR " + tablename
			    callback_func = function(returnedData) {
				console.log(returnedData)
				if(was_successful_call(returnedData)) {
				    term.echo(success_str)
				} else {
				    term.echo(fail_str)
				    handle_error(returnedData['error'], term)
				}
			    }
			    //TODO: change the dropdown menu to the table for
			    //      which we have created the model
			    JSONRPC_send_method("create_model", dict_to_send, callback_func)
			}
	    		else {
	    		    term.echo(window.wrong_command_format_str);
	    		    term.echo('Did you mean \'CREATE PTABLE <PTABLENAME> FROM <TABLE>\'?');
			}
	    		break
			
		    }
		    
		case "ANALYZE":
		    {
	    		echo_if_debug("ANALYZE", term)
	    		tempString = parseAnalyzeCommand(command)
	    		console.log(tempString)
			tablename = tempString["tableName"]
			chain_index = tempString["chainIndex"]
			iterations = tempString["iterations"]
			dict_to_send = {
 			    "tablename": tablename,
			    "chain_index": chain_index,
			    "iterations": iterations
			}
			success_str = ("ANALYZING " + tablename
				       + " CHAIN INDEX " + chain_index
				       + " FOR " + iterations + " ITERATIONS")
			JSONRPC_send_method("analyze", dict_to_send,
					    function(returnedData) {
						term.echo(success_str)
						console.log(returnedData)
					    }) 
			break
		    }
		    

		case "DROP":
		    {
	    		if (command_split[1].toUpperCase() == "PTABLE")
    			{ 
	    		    tempString = parseDropCommand(command)
			    tablename = tempString["tableName"]
			    dict_to_send = {"tablename": tablename}
			    JSONRPC_send_method("drop_tablename",
						dict_to_send,
						function(returnedData) {
						    // FIXME: actually verify that return value doesn't indicate error
						    term.echo("DROPPED PTABLE " + tablename)
						    console.log(returnedData)
						}) 
			    
			    delete preloadedDataFiles[tablename]
			    var select=document.getElementById('menu');
			    for (i=0;i<select.length;  i++) {
		    		if (select.options[i].value==tablename) {
		    		    select.remove(i);
		    		}
			    }
			} else {
    			    term.echo(window.wrong_command_format_str)
			    term.echo("Did you mean 'DROP PTABLE <PTALBENAME>?'")
    			}
    			break
		    }
		    
		case "DELETE":
		    {
	    		tempString = parseDeleteChainCommand(command)
	    		/*tempString = parseDropCommand(command)*/
	    		if (tempString == window.syntax_error_value){
			    term.echo(window.wrong_command_format_str);
			    break
			}
	    		console.log(tempString)
	    		tablename = tempString["tableName"]
			chain_index = tempString["chainIndex"]
			dict_to_send = {
	 		    "tablename": tablename,
			    "chain_index": chain_index
			}
	    		success_str = ("DELETED CHAIN " + tablename + " FOR " + chain_index)
			JSONRPC_send_method("delete_chain",
		    			    dict_to_send,
					    function(returnedData) {
						term.echo(returnedData);
						term.echo(success_str)
						console.log(returnedData)
						alert("Welcome!")
					    }) 
			break	
		    }
		    
		case "INFER": {
		    echo_if_debug("INFER", term)
		    dict_to_send = parseInferCommand(command)
		    if (dict_to_send == window.syntax_error_value) {
			term.echo(window.wrong_command_format_str);
			term.echo("Did you mean 'INFER col0, [col1, ...] FROM <PTABLE> [WHERE <WHERECLAUSE>] ...")
			term.echo("\t\t\t  WITH CONFIDENCE <CONFIDENCE> [LIMIT limit] [NUMSAMPLES numsamples]'?")
			break
		    } 
		    tablename = dict_to_send["tablename"]
		    newtablename = dict_to_send["newtablename"]
		    whereclause = dict_to_send["whereclause"]

		    success_str = ("INFERENCE DONE WITH CONFIDENCE: " + confidence
				  + " LIMIT " + dict_to_send['limit']
				  + " NUMSAMPLES " + dict_to_send['numsamples'])
		    fail_str = 'INFERENCE COMMAND FAILED'

		    callback_func = function(returnedData) {
			console.log(returnedData)
			if(was_successful_call(returnedData)) {
			    if(!newtablename){
		    		newtablename = tablename + '_inferred'
			    }
			    term.echo(success_str)
			    infer_result = returnedData['result']
			    parsed_infer_result = parse_infer_result(infer_result)
			    preloadedDataFiles[newtablename] = returnedData
			    set_menu_option(newtablename)
			    LoadToDatabaseTheCSVData(tablename, infer_result)
			} else {
			    term.echo(fail_str)
			    handle_error(returnedData['error'], term)
			}
		    }
		    JSONRPC_send_method("infer", dict_to_send, callback_func)
		    break
		    
		}
		    
		case "PREDICT": {
		    echo_if_debug("PREDICT", term)
		    dict_to_send = parsePredictCommand(command)
		    if(dict_to_send==window.syntax_error_value) {
			term.echo(window.wrong_command_format_str);
			term.echo("Did you mean 'PREDICT col0, [col1, ...] FROM <PTABLE>"
				  + " WHERE <WHERECLAUSE> TIMES times")
			break
		    }
		    tablename = dict_to_send['tablename']
		    times = dict_to_send['numpredictions']
		    success_str = ("PREDICTION DONE " + times 
				   + " TIMES FOR PTABLE " +  tablename)
		    callback_func = function(returnedData) {
			if(was_successful_call(returnedData)) {
			    console.log(returnedData)
			    term.echo(success_str)
			    predict_result = returnedData['result']
			    data = predict_result['data']
			    columns = predict_result['columns']
			    columns = convert_column_str_list(columns)
			    load_to_datatable(data, columns)
			} else {
			    term.echo('PREDICT COMMAND FAILED')
			    handle_error(returnedData['error'], term)
			}
		    }
		    JSONRPC_send_method("predict", dict_to_send, callback_func)
		    break		    
		}
		    
		case "GUESS": 
		    {
			echo_if_debug("GUESS", term)
			command_split = commandString.split(' ');
			tableName = get_el_after("FOR", command_split)
			JSONRPC_send_method("guessschema",
					    { "tablename":tableName},
					    function(returnedData) {
						typeDictToTable(returnedData)		
						console.log(returnedData)
						alert("Welcome!")
					    }) 
			break
			
		    }
		    
		default: {
		    if(command=='') { break }
		    dict_to_send = {"sql_command": command_split.join(' ')}
		    callback_func = function(returnedData) {
			console.log(returnedData)
			data = returnedData['result']['data']
			columns = returnedData['result']['columns']
			columns = convert_column_str_list(columns)
			load_to_datatable(data, columns)
		    }
		    JSONRPC_send_method("runsql", dict_to_send, callback_func)
		}
		}
	    } catch(e) { //catch the error in the terminal
		term.error(new String(e));
	    }
	} 
	else {
	    term.echo(''); 
	}
    }, {
	greetings: '',
	overflow : 'auto',
	name: 'SQL_demo',
	height: 100,
	width: 1200,
	prompt: 'predictive SQL>'});
});

preloadedDataFiles = new Object();

function menu_select(event) {
    if (event.target.selectedIndex == 0) {
	load_to_datatable([], [])
    } else {
	LoadToDatabaseTheCSVData(event.target.value, []);
    }
}

function set_kitware(img_str) {
    html_str = 'KITWARE'
    if(img_str.toUpperCase() != "NONE") {
	src_str = ' src="' + window.web_resource_base + img_str + '" '
	width_str = ' width="620" '
	height_str = ' height="380" '
	html_str = '<img ' + src_str + width_str + height_str + ' />'
    }
    $('#kitware').html(html_str)
}

function ProcessFiles(files_input) {
    for (var file_index = 0; file_index < files_input.length; file_index++) {
	var reader = new FileReader();
	reader.file_name = files_input[file_index].name.replace(".csv","");
	reader.onload = function(e) {
	    preloadedDataFiles[e.target.file_name] = e.target.result;
	    set_menu_option(e.target.file_name)
	}
	reader.readAsBinaryString(files_input[file_index])	
    }
}

function set_url_with_hostname(hostname) {
    if(typeof(hostname)==='undefined') {
	hostname = window.default_hostname
    }
    window.JSONRPC_URL = "http://" + hostname + ":8008"
    window.web_resource_base = "http://" + hostname + ":8000/"
}

function promptHost()
{    
    hostname = prompt("Please enter the host", window.default_hostname)
    set_url_with_hostname(hostname)
}
