export function Scroll(){
    const id=window.location.hash
    const scrollTarget = document.getElementById(id);
    if(scrollTarget !== null){
        scrollTarget.scrollIntoView({
            behavior:"smooth",
            block:"nearest"
        });
    }

}
export function ReloadPage(){
    location.reload();
}
