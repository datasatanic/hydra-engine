window.utils={
    initTooltip: (container = false) => {
        container ? document.querySelectorAll(container + ' .tooltip').forEach(value => value.remove()) : document.querySelectorAll('.tooltip').forEach(value => value.remove());
        let _container = container ? document.querySelector(container) : container;
        let tooltipTriggerList = container ? document.querySelectorAll(container + ' [data-bs-title]:not([data-bs-custom-class="custom-tooltip"])')
            : document.querySelectorAll('[data-bs-title]:not([data-bs-custom-class="custom-tooltip"])');
        [...tooltipTriggerList].map(tooltipTriggerEl => {

            return new bootstrap.Tooltip(tooltipTriggerEl, {
                customClass: "hydra-tooltip",
                trigger: 'hover',
                container: _container,
                delay: {"show": 750, "hide": 100}
            })
        });
    },
    collapseExpand: (id) =>{
        let element = document.getElementById(id)
        if(element){
            let bsCollapse = new bootstrap.Collapse(element);
            if(element.classList.contains("show")){
                bsCollapse.hide();
            }
            else{
                bsCollapse.show();
            }
        }
    }

}