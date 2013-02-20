library("rJava")
.jinit(classpath="MINE.jar")

###########################################
# MINE - runs MINE on a comma-separated
#  values (CSV) file. All parameters are as
#  in the Java version. The parameters
#  var1.id and var2.id are for use when
#  the analysis style specified requires
#  more information. For instance, since
#  style="master.variable" requires an
#  additional variable id (the id of the
#  master variable, you will need to
#  specify var1.id in this case.
#
#  As in the Java version, if you do not
#  specify a value for style, and you
#  specify a value for var1.id and not
#  var2.id, then style="master.variable"
#  will be assumed. If you do not specify a
#  value for style, and you specify values
#  for both var1.id and var2.id, then
#  style="one.pair" will be assumed.
#
# EXAMPLES:
#  MINE("Spellman.csv","all.pairs",0)
#  MINE("Spellman.csv",0)
#   will both run MINE on "Spellman.csv"
#   and have it analyze each variable only
#   against the 0-th variable.
#
#  MINE("Spellman.csv","one.pair",0,5)
#  MINE("Spellman.csv",0,5)
#   will both run MINE on "Spellman.csv"
#   and have it analyze only the 0-th
#   variable against the 5-th variable.
###########################################
MINE <- function (
		input.filename,
		style=c("master.variable", "all.pairs", "adjacent.pairs", "pairs.between", "one.pair"),
		var1.id=NA,
		var2.id=NA,
		required.common.vals.fraction=0,
		max.num.boxes.exponent=0.6,
		notify.wait=100,
		num.clumps.factor=15,
		debug.level=0,
		gc.wait=Inf,
		job.id
		) {

	printHeader()

	params <- getParams(input.filename, style, var1.id, var2.id, required.common.vals.fraction, max.num.boxes.exponent, notify.wait, num.clumps.factor, debug.level, gc.wait, job.id)

	# run the analysis
	cat("reading in dataset...\n")
	flush.console()

	dataset <- .jnew("data/Dataset",
				params$inputfile,
				params$analysisParams$mineParams$debug)

	cat("done.\n")
	flush.console()

	doAnalysis(dataset, params)
}

###########################################
# rMINE - runs MINE on an R matrix.
#  all parameters are as in MINE, except
#  that the name of the results file will
#  begin with output.prefix rather than
#  the name of the input file (since there
#  is no input file).
#
#  MINE assumes that each row of the
#  supplied matrix is a variable, and each
#  column is a record.
#
# EXAMPLE:
#  rMINE(matrix(1:10,2),"matrix",0)
#   will run MINE on matrix(1:10,2),
#   assuming that each of the two rows
#   in the matrix is a variable.
###########################################
rMINE <- function (
		data,
		output.prefix,
		style=c("master.variable", "all.pairs", "adjacent.pairs", "pairs.between", "one.pair"),
		var1.id=NA,
		var2.id=NA,
		required.common.vals.fraction=0,
		max.num.boxes.exponent=0.6,
		notify.wait=100,
		num.clumps.factor=15,
		debug.level=0,
		gc.wait=Inf,
		job.id
		) {
	printHeader()
	
	if(missing(output.prefix))
		stop("you must specify output.prefix so that I'll know what to name the output file!")

	params <- getParams(output.prefix, style, var1.id, var2.id, required.common.vals.fraction, max.num.boxes.exponent, notify.wait, num.clumps.factor, debug.level, gc.wait, job.id)

	# run the analysis
	cat("reading in dataset...\n")
	flush.console()

	data <- .jarray(data, dispatch=TRUE)

	dataset <- .jnew("data/Dataset",
				data, params$analysisParams$mineParams$debug)
	cat("done.\n")
	flush.console()

	doAnalysis(dataset, params)
}

printHeader <- function () {
	# print header
	cat(J("main/Analyze")$header())
	cat("\n\n")
	flush.console()
}

getParams <- function(
		input.filename,
		style=c("master.variable", "all.pairs", "adjacent.pairs", "pairs.between", "one.pair"),
		var1.id=NA,
		var2.id=NA,
		required.common.vals.fraction=0,
		max.num.boxes.exponent=0.6,
		notify.wait=100,
		num.clumps.factor=15,
		debug.level=0,
		gc.wait=Inf,
		job.id
		) {
	if (gc.wait==Inf) gc.wait <- J("java.lang.Integer")$MAX_VALUE
	else gc.wait <- as.integer(gc.wait)

	# create parameters object	
	if(missing(job.id)) {
		args <- .jarray(c(
				input.filename,
				style,
				var1.id,
				var2.id,
				paste("cv=", required.common.vals.fraction, sep = ""),
				paste("exp=", max.num.boxes.exponent, sep = ""),
				paste("notify=", notify.wait, sep = ""),
				paste("c=", num.clumps.factor, sep = ""),
				paste("d=", debug.level, sep = ""),
				paste("gc=", gc.wait, sep = "")
		))
	} else {
		args <- .jarray(c(
				input.filename,
				style,
				var1.id,
				var2.id,
				paste("cv=", required.common.vals.fraction, sep = ""),
				paste("exp=", max.num.boxes.exponent, sep = ""),
				paste("notify=", notify.wait, sep = ""),
				paste("c=", num.clumps.factor, sep = ""),
				paste("d=", debug.level, sep = ""),
				paste("gc=", gc.wait, sep = ""),
				paste("id=", job.id, sep = "")
		))
	}

	params <- .jnew("main/JobParameters", args)
	flush.console()

	#confirm parameters for user
	cat(params$toString())
	cat("\n")
	flush.console()

	params
}

doAnalysis <- function (dataset, params) {
	toAnalyze <- .jnew("analysis/VarPairQueue", dataset)
	
	params$analysisStyle$addVarPairsTo(toAnalyze, dataset$numVariables())
	
	a <- .jnew("analysis/Analysis", dataset, toAnalyze)

	cat("Analyzing...\n")
	flush.console()

	while(! a$varPairQueue()$isEmpty()) {
		# print a status update
		statusUpdate <- paste(a$numResults() + 1, " calculating: ", a$varPairQueue()$peek()$var1$name(), " vs ", a$varPairQueue()$peek()$var2$name(), "...\n", sep="")
		cat(statusUpdate)
		flush.console()

		# create a file containing the status update (for use when running on a cluster)
		write(statusUpdate, file=params$statusFileName())
			
		# analyze some more pairs
		a$analyzePairs(J("analysis.results/BriefResult")$class,
					params$analysisParams,
					params$notifyWait)
	}

	cat(paste(a$numResults(), " variable pairs analyzed.\n", "Sorting results in descending order...\n", sep=""))
	flush.console()

	results <- a$getSortedResults()

	cat("done. printing results\n")
	flush.console()

	#print the results
	repeat {
		if(J("main/Analyze")$printResults(results, params)) {
			break
		}
		else {
			n <- readline("writing results to output file failed. Perhaps it is locked in some way. Enter 1 to try again, 0 otherwise: ")
			if(n == 0) break
		}			
	}

	cat("Analysis finished. See file \"")
	cat(params$resultsFileName())
	cat("\" for output\n")
}
