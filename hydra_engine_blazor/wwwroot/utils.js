window.utils= {
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
    collapseExpand: (id) => {
        let element = document.getElementById(id)
        if (element) {
            let bsCollapse = new bootstrap.Collapse(element);
            if (element.classList.contains("show")) {
                bsCollapse.hide();
            } else {
                bsCollapse.show();
            }
        }
    },
    addListenersResize: (resizer, container) => {
        mousedownHandler = (event) => mousedown(event,container);
        resizer.addEventListener('mousedown', mousedownHandler)
    },
    clearListenersResize: (resizer) => {
        resizer.removeEventListener('mousedown', mousedownHandler)
        window.removeEventListener('mousemove', mousemoveHandler)
        window.removeEventListener('mouseup',stopResize)
        window.removeEventListener('mouseleave',stopResize)
        mousedownHandler = null;
        mousemoveHandler = null
    }
}
let mousedownHandler = null;
let mousemoveHandler = null;
function mousedown(e,container){
    e.preventDefault()
    mousemoveHandler = (event) => resize(event,container)
    window.addEventListener('mousemove', mousemoveHandler)
    window.addEventListener('mouseup', stopResize)
    window.addEventListener('mouseleave',stopResize)
}
function resize(e,container) {
    container.style.width = e.pageX - container.getBoundingClientRect().left + 'px'
}

function stopResize() {
    window.removeEventListener('mousemove', mousemoveHandler)
    window.removeEventListener('mouseup',stopResize)
    window.removeEventListener('mouseleave',stopResize)
}