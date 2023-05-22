// eel.expose(test_hello_js);
// function test_hello_js(attr) {
//     console.log("Hello from " + attr + "!")
// }
// eel.test_hello("Javascript. E")

/* TODO:
    "Image Not Found" / "Failed to generate" placeholder img
    Remove segment option
    Reorder segments option ( drag+drop sounds too hard?? )
*/

var segment_template;
var segment_seperator_template;
function initialize_template() {
    segment_template = document.querySelector(".segment");
    segment_seperator_template = document.querySelector(".segment-seperator-container");
    segment_template.remove();
    segment_seperator_template.remove();
}
initialize_template();

async function generate_sequence() {
    await eel.ags("test_js");
}

// Called automatically after generate_sequence populates
eel.expose(refresh_sequence);
function refresh_sequence() {
    console.log("Yeet! haha");
}

function clear_sequence() {

}

function make_segment(img, audio, text) {
    let new_segment_element = segment_template.cloneNode(true);
    if (img == false) img = "img/placeholder.png";
    new_segment_element.querySelector(".segment-img-src").src = img;
    new_segment_element.querySelector("source").src = audio;
    new_segment_element.querySelector(".segment-text").value = text;
    return new_segment_element;
}

eel.expose(append_segment);
function append_segment(img, audio, text) {
    let new_segment_element = make_segment(img, audio, text);
    document.querySelector(".editor").appendChild(new_segment_element);
    document.querySelector(".editor").appendChild(segment_seperator_template.cloneNode(true));
}

function append_segment_from_index(index) {
    len = eel.get_sequence_length()
    if (index < 0 || index >= len) return false;
    img = eel.get_segment_img(index);
    audio = eel.get_segment_audio(index);
    text = eel.get_segment_text(index);

    append_segment(img, audio, text);
}