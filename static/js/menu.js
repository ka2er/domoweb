(function(){
	var button = document.querySelector('#cn-button'),
    wrapper = document.querySelector('#cn-wrapper'),
    overlay = document.querySelector('#cn-overlay'),
    menuConfigure = document.querySelector('#menuConfigure'),
    menuWidgets = document.querySelector('#menuWidgets'),
    panelConfigure = document.querySelector('#panelConfigure'),
    main = document.querySelector('main');

	//open and close menu when the button is clicked
	var open = false;
	button.addEventListener('click', handler, false);
	wrapper.addEventListener('click', cnhandle, false);
	menuConfigure.addEventListener('click', configureHandler, false);
	menuWidgets.addEventListener('click', widgetsHandler, false);

	function cnhandle(e){
		e.stopPropagation();
	}

	function handler(e){
		if (!e) var e = window.event;
	 	e.stopPropagation();//so that it doesn't trigger click event on document

	  	if(!open){
	    	openNav();
	  	}
	 	else{
	    	closeNav();
	  	}
	}
	function openNav(){
		open = true;
	    button.innerHTML = "<span class='sr-only'>Close Menu</span>";
	    overlay.classList.add('on-overlay');
	    wrapper.classList.add('opened-nav');
	}
	function closeNav(){
		open = false;
		button.innerHTML = "<span class='sr-only'>Open Menu</span>";
	    overlay.classList.remove('on-overlay');
	    wrapper.classList.remove('opened-nav');
	}
	document.addEventListener('click', closeNav);

	function configureHandler(){
		panelConfigure.classList.remove('hidden');
		closeNav();
	}

	var widgetEdit = false;
	function widgetsHandler(){
		widgetEdit = !widgetEdit;
		if (widgetEdit) {
			document.querySelector('dmw-grid-layout').setAttribute('edit', true);
		} else {
			document.querySelector('dmw-grid-layout').removeAttribute('edit');
		}
		closeNav();
	}

})();
