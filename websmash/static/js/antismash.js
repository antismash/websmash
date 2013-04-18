function toggle_clusters() {
    var id = 2;
    var value_to_set = $('#cluster_1').prop('checked');
    if (!value_to_set) {
        value_to_set = false;
    }
    while($('#cluster_' + id).length) {
        $('#cluster_' + id).prop('checked', value_to_set);
        id++;
    }
}

function toggle_region() {
    if ($('#region').prop('checked')) {
        $('#region-input').show("fast");
    } else {
        $('#region-input').hide("fast");
    }
}

function toggle_legacy() {
    if ($('#legacy').prop('checked')) {
        $('#cluster_1').prop("checked", true);
        var id = 2;
        while($('#cluster_' + id).length) {
            $('#cluster_' + id).attr("disabled", true);
            id++;
        }
        $('#subclusterblast').prop("checked", false);
        $('#subclusterblast').attr("disabled", true);
        $('#inclusive').prop("checked", false);
        $('#inclusive').attr("disabled", true);
    } else {
        var id = 2;
        while($('#cluster_' + id).length) {
            $('#cluster_' + id).attr("disabled", false);
            id++;
        }
        $('#subclusterblast').prop("checked", true);
        $('#subclusterblast').attr("disabled", false);
        $('#inclusive').attr("disabled", false);
    }
}

function clear_upload() {
    $('#seq').val('');
    show_glimmer_if_needed();
}

function clear_ncbi() {
    $('#ncbi').val('');
}

function clear_sequence() {
    $('#sequence').val('');
}

function clear_prot_ncbi() {
    $('#prot-ncbi').val('');
}

function show_glimmer_if_needed() {
    var file = $('#seq').val();
    var euc  = $('#eukaryotic').prop('checked');

    // No need to show glimmer settings for eukaryotic fasta files
    if( is_fasta(file) && !euc ) {
        show_glimmer();
    } else {
        hide_glimmer();
    }
}


function seq_callback() {
    clear_ncbi();
    show_glimmer_if_needed();
}

function show_glimmer() {
    $('.dna_related').each(function(){
        $(this).show("fast");
    });
}

function hide_glimmer() {
    $('.dna_related').each(function(){
        $(this).hide("fast");
    });
}

function get_ext(file) {
    return file.split('.').pop();
}

function is_annotated(file) {
    var ext = get_ext(file.toLowerCase());
    var valid_exts = ['gb', 'gbk', 'genbank', 'emb', 'embl'];
    var res = false;
    for (i in valid_exts) {
        if (ext == valid_exts[i]) {
            res = true;
            break;
        }
    }
    return res;
}

function is_fasta(file) {
    var ext = get_ext(file.toLowerCase());
    var valid_exts = ['fasta', 'fas', 'fa', 'fna'];
    var res = false;
    for (i in valid_exts) {
        if (ext == valid_exts[i]) {
            res = true;
            break;
        }
    }
    return res;
}

function getFileSize() {
    var input, file;

    if (typeof window.FileReader !== 'function') {
        return 0;
    }

    input = $('#file');
    if (!input) {
        return 0;
    }
    else if (!input.files) {
        return 0;
    }
    else {
        file = input.files[0];
        return file.size;
    }
}

function verify_nucl_form() {
    var file = $('#seq').val();
    var ncbi = $('#ncbi').val();
    var from = $('#from').val();
    var to = $('#to').val();

    if( (file == '' || file == null) && (ncbi == '' || ncbi == null)){
        alert('No input file provided. Please enter NCBI number or upload your own file');
        return false;
    }

    if( !(is_annotated(file) || is_fasta(file)) && ncbi == '' ) {
        alert('Please provide EMBL/GenBank or nucleotide FASTA file');
        return false;
    }

    if((! $.isNumeric(from)) && (! from == '' && to == '')){
        alert("Please insert an integer number into the 'from' field.");
        return false;
    }

    if((! $.isNumeric(to)) && (! to == '' && to == '')){
        alert("Please insert an integer number into the 'to' field.");
        return false;
    }

    if(parseInt(from) > parseInt(to)){
        alert("Value in 'to' field should be higher than value in 'from' field.");
        return false;
    }

    return true;
}

function verify_prot_form() {
    var sequence = $('#sequence').val();
    var ncbi = $('#prot-ncbi').val();

    if( (sequence == '') && (ncbi == '')){
        alert('No input provided. Please enter NCBI number or paste your own sequence');
        return false;
    }

    if (ncbi.indexOf(';') > -1){
        alert('; found in NCBI ID list, please use a plain comma (,) to separate IDs');
        return false;
    }

    if (ncbi.indexOf(' ') > -1 || ncbi.indexOf('\t') > -1){
        alert('whitespace found in NCBI ID list, please use a comma (,) to separate IDs');
        return false;
    }
    return true;
}

function update_status(url) {
    $.getJSON(url, function(json) {
        $("#server-status").html(json.status);
        $("#queue-length").html(json.queue_length);
        $("#running-jobs").html(json.running);
    });
}

function repeatedly_update_status(url) {
    update_status(url);
    $.timer(10000, function(timer) {
        update_status(url);
    });
}

function display_notices(url) {
    $.getJSON(url, function(json) {
        if (json.notices.length < 1) {
            return;
        }
        for (var n in json.notices) {
            var notice_data = json.notices[n];
            var notice = $('<div>');
            notice.addClass('alert alert-block');
            notice.addClass('alert-' + notice_data.category);
            notice.append('<a href="#" class="close" data-dismiss="alert">&times;</a>');
            var teaser = $('<h4>');
            teaser.text(notice_data.teaser);
            notice.append(teaser);
            notice.append(document.createTextNode(notice_data.text));
            $('#notice-container').append(notice);

        }
    });
}

function display_job_status(url, img_dir) {
    $.getJSON(url, function(json) {
        $('body').data('job_status', json.short_status);
        $("#last-changed").text(json.last_changed);
        var stat = json.status;
        stat = stat.replace(/\n/g, '<br>');
        $("#status").html(stat);
        $("#status-img").attr('src', img_dir + '/' + json.short_status + '.gif');
        if (json.status != 'done') {
            return;
        }
        var result = $('<a>');
        result.attr('href', json.result_url);
        result.text('result');
        $('#result-link').append('See the ');
        $('#result-link').append(result);
        $.timer(5000, function(timer) {
            window.location.href = json.result_url;
        });
    });
}

function repeatedly_update_job_status(url, img_dir) {
    $.timer(10000, function(timer) {
        display_job_status(url, img_dir);
        var stat = $('body').data('job_status');
        if ( stat == 'done' || stat == 'failed' ) {
            timer.stop();
        }
    });
}
