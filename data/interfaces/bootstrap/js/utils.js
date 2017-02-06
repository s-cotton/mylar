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