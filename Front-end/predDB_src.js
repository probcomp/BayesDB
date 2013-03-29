			
// jQuery(document.getElementById("example").rows[2].cells[1]).addClass("redText")
// jQuery(document.getElementById("example").rows[2].cells[1]).removeClass("redText")

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
			
			
			
			function CSVtoJSON(csvFile){
				var arrayDataSet = $.csv.toArrays(csvFile);
				numCols = arrayDataSet[0].length - 1 // removing the first column for the row names 
				numRows = arrayDataSet.length - 1
				var indxToColDict = {}
				var colToIndxDict = {}
				var columnMetadata = {}
				var columnMetadataArray = []
				var indxToRowDict = {}
				var rowToIndxDict = {}
				dataJSON = arrayDataSet.slice(1)
				newDataJSON = []
				YDict = {}
			    for (var i = 0; i < numCols; i++){
			    	indxToColDict[i] = arrayDataSet[0][i + 1]
			    	colToIndxDict[arrayDataSet[0][i + 1]] = i
			    	columnMetadata["modeltype"] = "normal_inverse_gamma"
			    	columnMetadata["value_to_code"] = {}
			    	columnMetadata["code_to_value"] = {}
			    	columnMetadataArray.push(columnMetadata)
				} 
				
				for (var j = 0; j < numRows; j++){
					indxToRowDict[j] = arrayDataSet[j + 1][0]
					rowToIndxDict[arrayDataSet[j + 1][0]] = j
					newDataJSON.push(dataJSON[j].slice(1))
				}
				
				for (var i = 0; i < numCols; i++){
					for (var j = 0; j < numRows; j++){
						YDict[[j, i]] = arrayDataSet[j + 1][i + 1]
					}
				} 
				var M_c = {"name_to_idx": colToIndxDict, "idx_to_name": indxToColDict,
						"column_metadata": columnMetadataArray};
				var M_r = {"name_to_idx": rowToIndxDict, "idx_to_name": indxToRowDict}
				var T = {"dimensions":[numRows, numCols], "orientation": "row_major",
					    "data":newDataJSON}
				var Y = YDict
				var q = findNaNValuesInCSV(csvFile)
				console.log(q)
				return {"M_c":M_c, "M_r":M_r, "T":T, "Y":Y,  "X_L":"", "X_D":"", "kernel_list":"", "n_steps":"",
					"c":"", "r":"","max_iterations":"", "max_time":"", "q":q}
			}
			
			
			function CSVtoSQLFormat(csvFile, tableName){
				var dataSetDict = $.csv.toObjects(csvFile);
				arrayDataSet = $.csv.toArrays(csvFile);
				numCols = arrayDataSet[0].length - 1
				numRows = dataSetDict.length - 1
				newDataCol1Removed = []
				var columnDefs = {}
				var columnDefsDict = {}
				var tableDict = {}
				for (var i = 0; i < numCols + 1; i++){
			    	columnDefs[arrayDataSet[0][i]] = { type: "Number" }
				} 
				
				for (var j = 0; j < numRows; j++){
					/* delete dataSetDict[j]["NAME"] */
					newDataCol1Removed.push(dataSetDict[j])
				} 
				columnDefsDict[tableName] = columnDefs
				tableDict[tableName] = newDataCol1Removed
				
				return {"dataTable":tableDict, "columnDefs":columnDefsDict}
			}
			
			
			function JSONToSQL(JSONString, tableName){
				obj = JSONString
				dataTable = obj.T.data //Transform later
				/* numMissingVals = obj.e.length
				listofMissingVals = obj.e
				for (var i in listofMissingVals){
						dataTable[i.split(',')[0], i.split(',')[1]] = listofMissingVals[i]  
				}  */
				var columnDefs = {}
				var columnDefsDict = {}
				var tableDict = {}
				var dataArrayofDicts = []
				rowNamesDict = obj.M_r.idx_to_name
				colNamesDict = obj.M_c.idx_to_name
				numRows = obj.T.dimensions[0]
				numCols = obj.T.dimensions[1]
				dataTableEncoded = obj.T.data //Need to transform 
				columnDefsDict = {}
				tableDict = {}
				
				columnDefs["NAME"] = { type: "Number" }
				for (var i = 1; i < numCols; i++){
			    	columnDefs[colNamesDict[i]] = { type: "Number" }
				} 
				
				for (var j = 0; j < numRows; j++){
					tempRowDict = {}
					for (var k = 0; k < numCols; k++){
						tempRowDict[colNamesDict[k]] = dataTableEncoded[j][k]
					}
					dataArrayofDicts.push(tempRowDict)
				}
				columnDefsDict[tableName] = columnDefs
				tableDict[tableName] = dataArrayofDicts
				return {"dataTable":tableDict, "columnDefs":columnDefsDict}
			}
			
			
			
/* JSON functions*/
			function JSONRPC_init() {
	 	 		JSONRPC_URL = "http://localhost:8007/"
		 	 	JSONRPC_ID = 0				
			}
			
			function JSONRPC_send_method(method_name, parameters, function_to_call) {
	 	 		 JSONRPC_ID += 1
	 	 		 data_in =
	 	 		   { id : toString(JSONRPC_ID),
	 	 		     jsonrpc : "2.0",
	 	 		     method : method_name,
	 	 		     params : parameters }
	 	 		 $.ajax({
	 	 				url: JSONRPC_URL, 
	 	 				type: 'PUT', 
	 	 				data: JSON.stringify(data_in),
	 	 				dataType: 'json', 
	 	 				async: false,	
	 	 				crossDomain: true,
	 	 				success:function(data) {
	 	 					function_to_call(data)
	 	 				},
	 	 				error: function(httpRequest, textStatus, errorThrown) {
	 	 					console.log(httpRequest)
	 	 					alert("Sorry, some error has happened.")
	 	 				},
	 	 		       		complete: function() {
	 	 		            		//console.log('COMPLETE');
	 	 		       		}		
	 	 			});			    
			}
			
			

/* Parser functions*/
			function parseCommand(commandString){
				if (command.split(' ')[0]=="SELECT"){
					inferCommandParsed = commandString.split(' ');
			    	confidence = inferCommandParsed[$.inArray("CONFIDENCE", inferCommandParsed) + 1]
			    	resolution = inferCommandParsed[$.inArray("RESOLUTION", inferCommandParsed) + 1]
				}
			}
			
			
			
/* Loading and jqueries functions*/
			function LoadToDatabaseTheCSVData(data) {
 	 			window.masterData = data
	        	JSONDict = CSVtoJSON(data)
	        	test2 = JSONToSQL(JSONDict, "dha")
	        	
	        	/* JSONRPC_init()
	 	 		JSONRPC_send_method("initialize",
				            { M_c: JSONDict["M_c"], M_r: JSONDict["M_r"], T: JSONDict["T"], i: "i" },
				            function(data) {
				            	console.log(data)
				            	alert("Welcome!")
				            }) */	
	            /* 
	 	 		JSONRPC_send_method("initialize",
				            { M_c: JSONDict["M_c"], M_r: JSONDict["M_r"], T: JSONDict["T"], i: "i" },
				            function(data) {
				            	console.log(data)
				            	alert("Welcome!")
				            	STORE THE JSON IN A GLOBAL VAR
				            }) */
				            
	     		var aDataSet = $.csv.toArrays(data); 
	     		var columns = new Array();
				var counter = 0;
				for (var c in aDataSet[0]){
				    	columns[counter] = { "sTitle": aDataSet[0][c] , "sClass": "center"}
				    	counter += 1
				}
				aDataSet.shift()  
	     		$('#dynamic').html( '<table cellpadding="0" cellspacing="0" border="0" class="display" id="example"></table>' );
				console.log($('#example'))
				$('#example').dataTable( {
					"aaData": aDataSet,
					"aoColumns": columns 
				} );
				jQuery(document.getElementById("example").rows[2].cells[1]).addClass("redText")
 			}
			
			
			
			
	 	 	$(document).ready(function() {	 
	 	 		window.commandHistory = [];
	 	 		window.scrollChange = false
                $('#range_confidence').rangeinput({progress: true, max: 100})
                $("#range_confidence").change(function(event, value) {
                    window.scrollChange = true
                });
                $('#range_resolution').rangeinput({progress: true, max: 100})
                $("#range_resolution").change(function(event, value) {
                	 window.scrollChange = true
                });
                   window.sliders.style.display = 'none';
			} );  
			
	 	 	
		    jQuery(function($, undefined) {
		        $('#term_demo').terminal(function(command, term) {
		        	mydat = CSVtoSQLFormat(masterData, "dha")
		        	if (command !== ''){
		        		commandHistory.push(command)
		        	}
		        if (command !== '' || commandHistory.length != 0) {
		        	
		        try {
		        	var tableData = mydat["dataTable"]
		        	var columnDefs = mydat["columnDefs"]
				
			    var queryLang = TrimPath.makeQueryLang(columnDefs);
			    if (command.split(' ')[0]=="SELECT")
			    	{
			    	   var statement = queryLang.parseSQL(command);
					   var result = statement.filter(tableData);
					   window.sliders.style.display = 'none';
					   window.scrollChange = false
					   commandHistory.length = 0
			    	}
			    else  
			    	{ var confidence = 0
			    	  var resolution = 0
			    	if(window.scrollChange == false){
			    		inferCommandParsed = commandHistory[commandHistory.length - 1].split(' ');
				    	confidence = inferCommandParsed[$.inArray("CONFIDENCE", inferCommandParsed) + 1]
				    	resolution = inferCommandParsed[$.inArray("RESOLUTION", inferCommandParsed) + 1]
				    	window.sliders.style.display = '';
				    	$("#range_confidence").val(confidence) 
				    	$("#range_resolution").val(resolution) 
			    	} if(window.scrollChange == true){
			    		confidence =  $("#range_confidence").val()
			    		resolution =  $("#range_resolution").val()
			    	}
			    	/* send these two to backend and retrieve new table */
			    	tableData =  { 
		        	        Invoice  : [ { "id": 1, "total": 100, "custId": 10 }]}
			    	
			    	command = commandHistory[commandHistory.length - 1]
			    	command = command.replace("INFER","SELECT");
			    	command = command.substring(0, command.indexOf("WITH") - 1); 
			    	var statement = queryLang.parseSQL(command);
					var result = statement.filter(tableData);  
			    	}
			    
			    var out = "";
			    for (var r = 0; r < result.length; r++) {
			        for (var c in result[r])
			            /* out += c + ": " + result[r][c] + ", "; */
			        	out += result[r][c] + ", ";
			        out += "\n";
			    }
			    var aDataSet = $.csv.toArrays(out); 
			    
			    var columns = new Array();
			    var counter = 0;
			    for (var c in result[0]){
			    	columns[counter] = { "sTitle": c , "sClass": "center"}
			    	counter += 1
			    }
			    
	     		$('#dynamic').html( '<table cellpadding="0" cellspacing="0" border="0" class="display" id="example"></table>' );
				$('#example').dataTable( {
					"aaData": aDataSet,
					"aoColumns": columns
				} );
				
		        if (result !== undefined) {
		        /* term.echo(new String(result)); */
		        }
		        } catch(e) {
		        term.error(new String(e));
		        }
		        } else {
		        /* term.echo(''); */
		        }
		        }, {
		        greetings: '',
		        name: 'SQL_demo',
		        height: 100,
		        width: 1000,
		        prompt: 'SQL Command>'});
		        });
			
		function ProcessFiles(files_input) {
			for (var file_index = 0; file_index < files_input.length; file_index++) {
				console.log(files_input[0].name);
				var reader = new FileReader();
				reader.onload = function(e) {
					LoadToDatabaseTheCSVData(e.target.result)
				}
				reader.readAsBinaryString(files_input[file_index])	
			}
		}