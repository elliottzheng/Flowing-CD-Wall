last_album_name = '';


function check_album_name() {
    fetch('current.json',{ cache: "no-store" }).then(response => {
        response.json().then(data => {
            console.log(data);
            if (last_album_name == data['album_name']) {
                return;
            }
            if (last_album_name != '') {
                let img = document.querySelector('img[alt="'+last_album_name+'"]');
                if (img) {
                    //red border
                    // img.border = '5px solid red';
                    // remove border
                    img.border = '';

                    // img.classList.remove('animate__heartBeat');
                    // // animate__infinite	infinite
                    // img.classList.remove('animate__infinite');
                }
            }
            // find img alt == data['album_name']
            let img = document.querySelector('img[alt="'+data['album_name']+'"]');
            if (img) {
                //append .demo1 to img
                // img.classList.add('animate__heartBeat');
                // img.classList.add('animate__infinite');
                img.border = '5px solid red';
                // <span class="Scan"></span>
                //append this span after img
                // let span = document.createElement('span');
                // span.classList.add('Scan');
                // img.after(span);

            }
            last_album_name = data['album_name'];
        });
    })
}
// check_album_name();
// setInterval(check_album_name, 5000);