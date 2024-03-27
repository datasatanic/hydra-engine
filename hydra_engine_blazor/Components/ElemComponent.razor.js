export function Scroll(id){
    const scrollTarget = document.getElementById(id);
    if(scrollTarget !== null){
        scrollTarget.scrollIntoView({
            behavior:"smooth",
            block:"center",
        });
    }
}
export function setFullHeight(textareaElement){
    if (textareaElement){
        console.log(textareaElement.scrollHeight)
        if(textareaElement.scrollHeight > textareaElement.offsetHeight){
            textareaElement.style.height = textareaElement.scrollHeight + 2 + "px";
        }
        
    }
}