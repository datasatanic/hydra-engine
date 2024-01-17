export function Scroll(id){
    const scrollTarget = document.getElementById(id);
    if(scrollTarget !== null){
        scrollTarget.scrollIntoView({
            behavior:"smooth",
            block:"center",
        });
    }
}