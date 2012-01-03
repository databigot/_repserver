formatters = {
		jelinkto: function(value) {
			return '<a class="grid-link" href="' + value.linkto + '"> ' + value.show + ' </a>';
		},
        actions: function(value) {
            var content = '', pair;
            if(value.label) {
                content += '<div class="grid-row-label">' + value.label + '</div>';
            }
            content += '<div class="grid-row-actions">';
            for(var i = 0; i < value.actions.length; i++) {
                content += '<span class = "grid-row-action-container">';
                pair = value.actions[i];
                content += '<a class="grid-row-link';
                if(pair.disabled) {
                    content += ' grid-row-link-disabled';
                }
                content += '"';
                if(!pair.disabled){
                    if(pair.url) {
                        content += ' href="' + pair.url + '"';
                        if(pair.external) {
                            content += ' target="_blank"';
                        }
                    } else {
                        content += ' onclick="' + pair.action + '"';
                    }
                }
                content += '>' + pair.label + '</a>';
                if(pair.tooltip) {
                    content += '<div class="tooltip tooltip-content">';
                    content += pair.tooltip + '</div>';
                }
                content += '</span>';
            }
            return content + '</div>';
        },
        buttons: function(value) {
            var buttons = [], items = value.split(';'), pair, script;
            for(var i = 0; i < items.length; i++) {
                pair = items[i].split('=');
                if(pair[1].slice(0, 11) == 'javascript:') {
                    script = pair[1];
                } else {
                    script = "javascript:window.location='" + pair[1] + "';";
                }
                buttons.push('<button class="grid-row-button" onclick="' + script + '">' + pair[0] + '</button>');
            }
            return buttons.join('');
        },
		channels: function(value) {
            var output = '<div class="offer-channels-container">\
                <span class="channel-label">' + value.label + '</span>';
            var other_channels_length = value.channels_labels.length - 1;
            if(other_channels_length > 0) {
                var other_channels_label = '+ ' + other_channels_length + ' more <span>?</span>';
                output += '<div class="other-channels">' + other_channels_label + '</div>';
                output += '<div class="tooltip offer-channels"><div class="tooltip-content">Channels: ';
                output += value.channels_labels.join(", ");
                output += '</div></div>';
			}
            output += '</div>';
			return output;
		},
        currency: function(value) {
            value = parseFloat(value).toFixed(2);
            return '<span class="number currency">$' + value + '</span>';
        },
        currency_negative: function(value) {
            value = parseFloat(value).toFixed(2);
            return '<span class="number currency-negative">$' + value + '</span>';
        },
        currency_long: function(value) {
            value = parseFloat(value).toFixed(4);
            return '<span class="number currency">$' + value + '</span>';
        },
        integer: function(value) {
            return '<span class="number">' + parseFloat(value).toFixed(0) + '</span>';
        },
        links: function(value) {
            var anchors = [], links = value.split(';'), pair = null;
            for(var i = 0; i < links.length; i++) {
                pair = links[i].split('=');
                anchors.push('<a class="grid-row-link" onclick="' + pair[1] + '">' + pair[0] + '</a>');
            }
            return anchors.join('');
        },
		linkto: function(value) {
			return '<a class="grid-link" href="' + value.linkto + '"> ' + value.show + ' </a>';
		},
        nonblank: function(value) {
            return (value.length > 0) ? value : '-';
        },
        percentage: function(value) {
            return '<span class="number">' + Math.floor(parseFloat(value) * 100) + '%' + '</span>';
        },
        percentage_decimal: function(value) {
            return '<span class="number">' + (100*parseFloat(value)).toFixed(2) + '%' + '</span>';
        },
        progress: function(value) {
            var blocks = '', progress = '';
            var progress_step_disabled_tooltip_icon = '<span class="step-disabled-tooltip-icon">'+
                '<span>?</span></span>';
            for(var i = 0; i < value.value; i++) {
                blocks += '<div></div>';
            }
            var width = (value.max * 11) + 'px';
            progress = '<div class="progress-blocks" style="width:' + width + ';">' + blocks + '</div>';
            if(value.label) {
                progress += '<div class="progress-label">' + value.label + '</div>';
            }
            if(value.back) {
                var progress_step_class = 'disabled';
                if(value.back.enabled) {
                    progress_step_class = 'enabled';
                }
                progress += '<a class="progress-step-back grid-row-link ' + progress_step_class + '" ' +
                    'data-offer_name="' + value.back.offer_name + '" ' +
                    'data-status="' + value.back.status + '" ' +
                    'data-publisher_name="' + value.publisher_name + '">';
                if(value.back.enabled) {
                    progress += '<span class="step-back-action-icon"><span>&lt;</span></span>';
                }
                else {
                    progress += progress_step_disabled_tooltip_icon;
                }
                progress += '<span class="status-label">' + value.back.label + '</span></a>';
            }
            if(value.forward) {
                var progress_step_class = 'disabled';
                if(value.forward.enabled) {
                    progress_step_class = 'enabled';
                }
                progress += '<a class="progress-step-forward grid-row-link ' + progress_step_class + '" ' +
                    'data-offer_name="' + value.forward.offer_name + '" ' +
                    'data-status="' + value.forward.status + '" ' +
                    'data-publisher_name="' + value.publisher_name + '">';
                progress += '<span class="status-label">' + value.forward.label + '</span>';
                if(value.forward.enabled) {
                    progress += '<span class="step-forward-action-icon"><span>&gt;</span></span>';
                }
                else {
                    progress += progress_step_disabled_tooltip_icon;
                }
                progress += '</a>';
            }
            return progress;
        },
        vetted: function(value) {
            if(value.editable) {
                output = '<span class="vetted-label">' + value.label + '</span>';
                output += '<a class="change-vetted-action grid-row-link enabled" \
                    data-offer_name="' + value.offer_name + '" \
                    data-publisher_name="' + value.publisher_name + '" \
                    data-vetted="' + value.change_vetted + '">\
                    (Change)</a>';
            }
            else {
                output = '<span class="vetted-label">' + value.label + '</span>';
            }
            return output;
        }
    };

