export function addListenersResize(resizer){
    resizer.addEventListener('mousedown', mousedown)
}
function mousedown(e){
    e.preventDefault()
    window.addEventListener('mousemove', resize)
    window.addEventListener('mouseup', stopResize)
}
function resize(e) {
    const element = document.querySelector(".menu-container");
    element.style.width = e.pageX - element.getBoundingClientRect().left + 'px'
}

function stopResize() {
    window.removeEventListener('mousemove', resize)
}
export function clearListenersResize(resizer){
    resizer.removeEventListener('mousedown', mousedown)
    window.removeEventListener('mousemove', resize)
    window.removeEventListener('mouseup',stopResize)
}
