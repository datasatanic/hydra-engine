export function Scroll(id){
    const scrollTarget = document.getElementById(id);
    console.log(id)
    console.log(scrollTarget)
    if(scrollTarget !== null){
        scrollTarget.scrollIntoView({
            behavior:"smooth",
            block:"center",
        });
    }
}