var mylar = mylar || {};
mylar.utils = {};
mylar.utils.filterCollection = function(collection, filterValue) {
    if (filterValue == "") return [];
    return collection.filter(function(data) {
        return _.some(_.values(data.toJSON()), function(value) {
           if (_.isNumber(value)) value = value.toString();
           if (_.isString(value)) return value.toLowerCase().indexOf(filterValue) != -1;
           return false;
        });
    });
}

Backbone.Collection.prototype.filterValues = function(filterValues) {
    return mylar.utils.filterCollection(this, filterValues);
}

mylar.utils.getPublisherImage = function(publisher){
	switch( publisher ){
		case 'DC Comics': return {
				image : "interfaces/default/images/publisherlogos/logo-dccomics.png",
				name  : "DC",
				height: "50",
				width : "50",
			}; break;
		case 'Marvel': return {
				image : "interfaces/default/images/publisherlogos/logo-marvel.jpg",
				name  : "Marvel",
				height: "50",
				width : "100",
			}; break;
		case 'Image': return {
				image : "interfaces/default/images/publisherlogos/logo-imagecomics.png",
				name  : "Image",
				height: "100",
				width : "50",
			}; break;
		case 'Dark Horse Comics':
		case 'Dark Horse': return {
				image : "interfaces/default/images/publisherlogos/logo-darkhorse.png",
				name  : "Darkhorse",
				height: "100",
				width : "75",
			}; break;
		case 'IDW Publishing': return {
				image: "interfaces/default/images/publisherlogos/logo-idwpublish.png",
				name: "IDW",
				height: "50",
				width: "100",
			}; break;
		case 'Icon': return {
				image : "interfaces/default/images/publisherlogos/logo-iconcomics.png",
				name  : "Icon",
				height: "50",
				width : "100",
			}; break;
		case 'Red5': return {
				image: "interfaces/default/images/publisherlogos/logo-red5comics.png",
				name  : "Red5",
				height: "50",
				width : "100",
			}; break;
		case 'Vertigo': return {
				image : "interfaces/default/images/publisherlogos/logo-vertigo.jpg",
				name  : "Vertigo",
				height: "50",
				width : "100",
			}; break;
		case 'ShadowLine': return {
				image : "interfaces/default/images/publisherlogos/logo-shadowline.png",
				name  : "Shadowline",
				height: "75",
				width : "100",
			}; break;
		case 'Archie Comics': return {
				image : "interfaces/default/images/publisherlogos/logo-archiecomics.jpg",
				name  : "Archie",
				height: "75",
				width : "75",
			}; break;
		case 'Oni Press': return {
				image : "interfaces/default/images/publisherlogos/logo-onipress.png",
				name  : "Oni Press",
				height: "50",
				width : "100",
			}; break;
		case 'Tokyopop': return {
				image : "interfaces/default/images/publisherlogos/logo-tokyopop.jpg",
				name  : "Tokyopop",
				height: "50",
				width : "100",
			}; break;
		case 'Midtown Comics': return {
				image : "interfaces/default/images/publisherlogos/logo-midtowncomics.jpg",
				name  : "Midtown",
				height: "50",
				width : "100",
			}; break;
		case 'Boom! Studios': return {
				image : "interfaces/default/images/publisherlogos/logo-boom.jpg",
				name  : "Boom! Studios",
				height: "50",
				width : "100",
			}; break;
		case 'Skybound': return {
				image : "interfaces/default/images/publisherlogos/logo-skybound.jpg",
				name  : "Skybound",
				height: "50",
				width : "100",
			}; break;
		case 'Vertigo': return {
				image : "interfaces/default/images/publisherlogos/logo-dynamite.jpg",
				name  : "Dynamite",
				height: "50",
				width : "100",
			}; break;
		case 'Top Cow': return {
				image : "interfaces/default/images/publisherlogos/logo-topcow.gif",
				name  : "Top Cow",
				height: "75",
				width : "100",
			}; break;
		case 'Dynamite Entertainment': return {
				image : "interfaces/default/images/publisherlogos/logo-dynamite.png",
				name  : "Dynamite",
				height: "50",
				width : "100",
			}; break;
		case 'Cartoon Books': return {
				image : "interfaces/default/images/publisherlogos/logo-cartoonbooks.jpg",
				name  : "Cartoon Books",
				height: "75",
				width : "90",
			}; break;
		case 'Valiant': return {
				image : "interfaces/default/images/publisherlogos/logo-valiant.png",
				name  : "Valiant",
				height: "100",
				width : "100",
			}; break;
		case 'Action Lab': return {
				image : "interfaces/default/images/publisherlogos/logo-actionlabs.png",
				name  : "Action Lab",
				height: "100",
				width : "100",
			}; break;
		case 'Zenescope Entertainment': return {
				image : "interfaces/default/images/publisherlogos/logo-zenescope.png",
				name  : "Zenescope",
				height: "100",
				width : "160",
			}; break;
		default:
			return false;
	}
};

Handlebars.registerHelper('if', function(conditional, options) {
  if(conditional) {
    return options.fn(this);
  } else {
    return options.inverse(this);
  }
});