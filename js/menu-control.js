function show_docs_menu(){
	$('#mobile-button').show();
	$('#mobile-sidebar').show();
	window.menu_is_shown = false;
	
	$('#mobile-button').css('left','0px');
	$('#mobile-button').html('<span class="glyphicon glyphicon-th-list"></span>');
	$('#mobile-sidebar').css('left','-220px');	
	window.menu_is_shown = false;
}

function link_menu_button(){
	$('.main').click(function(){
		if(window.menu_is_shown) {
			$('#mobile-button').css('left','0px');
			$('#mobile-button').html('<span class="glyphicon glyphicon-th-list"></span>');
			$('#mobile-sidebar').css('left','-220px');	
			$('div.main').css('margin-left','0');
			window.menu_is_shown = false;
		}
	});
	$('#mobile-button').click(
		function(){

			if(window.menu_is_shown) {
				$('#mobile-button').css('left','0px');
				$('#mobile-button').html('<span class="glyphicon glyphicon-th-list"></span>');
				$('#mobile-sidebar').css('left','-220px');	
				$('div.main').css('margin-left','0');
				window.menu_is_shown = false;
			}else{
				$('#mobile-button').css('left','220px');
				$('#mobile-button').html('<span class="glyphicon glyphicon-remove"></span>');
				$('#mobile-sidebar').css('left','0px');	
/* 					$('div.main').css('margin-left','220px'); */
				window.menu_is_shown = true;
			}	
		}
	);
};

function get_menu_items_docs(){
	var menu = $('#mobile-sidebar-ul');
	$('div.layout h1, div.layout h2, div.layout h3').each(function(){
		var header_text = $(this).html();
		var anchor_id = header_text.replace(/[^A-Z0-9]+/ig, "_");
		$(this).prepend('<a id="' + anchor_id + '">');
		menu.append('<li><a href="#' + anchor_id + '">' + header_text + '</a></li>');
	});
}


function get_menu_items_examples(){
	var menu = $('#mobile-sidebar-ul');
	$('div.layout h1').each(function(){
		var header_text = $(this).html();
		var anchor_id = header_text.replace(/[^A-Z0-9]+/ig, "_");
		$(this).prepend('<a id="' + anchor_id + '">');
		menu.append('<li><a href="#' + anchor_id + '">' + header_text + '</a></li>');
	});
}