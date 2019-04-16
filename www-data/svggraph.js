function update_json(trg,src){
    for(let key in src){
        trg[key] = src[key]
    }
    return trg
}
var svggraph_defaults={
    resolution:1,
    background:"#e1e1e1"
};
class SVGGraphAxis {
    constructor(type,graph,name,options) {
        this.type= (type==="x"?0:type==="y"?1:1);
        this.options={
            position:"left",
            color:"#000000",
            autoscale:true,
            dx:0,
            dy:0,
            ticks:{
                major:{
                    count:5,
                    color:null,
                    size:20,
                    inside:true,
                    outside:true,
                },
                minor:{
                    count:10,
                    color:null,
                    size:10,
                    inside:true,
                    outside:true,
                }
            },
            formatter:function (number) {
                return number.toExponential(2);
            }
        };
        this.options = update_json(this.options,options);
        this.name=name;
        this.graph=graph;
        this.svg=graph.svg.group();
        this.axis_line=this.svg.line(
            0,
            0,
            svggraph_defaults.resolution,
            svggraph_defaults.resolution
        );
        this.tick_group=this.svg.group();
        this.datasets=[];
        this.checkscale();
        this.redraw();
    }

    add_dataset(dataset){
        this.datasets.push(dataset);
    }
    color_as_dataset(index=0){
        if(index>=this.datasets.length)
            throw ("Dataset index to high");

        this.options.color=this.datasets[0].options.color
    }
    remove_dataset(dataset){
        var index = this.datasets.indexOf(dataset);
        if (index > -1) {
            this.datasets.splice(index, 1);
        }
    }
    redraw(){
        let rightspace=0;
        let leftspace=0;
        let topspace=0;
        let bottomspace=0;
        let vb = this.graph.svg.attr("viewBox");


        this.axis_line.attr({
            stroke: this.options.color,
            x1:this.type?
                (this.options.position==="right"?this.graph.options.inner_width+this.options.dx:0+this.options.dx):
                0+this.options.dx,
            y1:this.graph.options.inner_height,
            x2:this.type?
                (this.options.position==="right"?this.graph.options.inner_width+this.options.dx:0+this.options.dx)
                :this.graph.options.inner_width+this.options.dx,
            y2:this.type?0:this.graph.options.inner_height
        });
        this.tick_group.remove();
        this.tick_group=this.svg.group();
        for(let i=0;i<this.options.ticks.major.count;i++){
            let thistickgroup=this.tick_group.group();
            let xbase=this.type?
                parseInt(this.axis_line.attr('x1')):
                (parseInt(this.axis_line.attr('x1'))+
                    (i)*(
                        parseInt(this.axis_line.attr('x2'))-
                        parseInt(this.axis_line.attr('x1')))/(this.options.ticks.major.count-1)
                );
            let ybase=this.type?
                (parseInt(this.axis_line.attr('y1'))+(i)*(
                    parseInt(this.axis_line.attr('y2'))-parseInt(this.axis_line.attr('y1'))
                )/(this.options.ticks.major.count-1)):
                parseInt(this.axis_line.attr('y1'));
            thistickgroup.line(
               this.type?(xbase-this.options.ticks.major.size):xbase,
               this.type?ybase:(ybase-this.options.ticks.major.size),
               this.type?(xbase+this.options.ticks.major.size):xbase,
               this.type?ybase:(ybase+this.options.ticks.major.size),
           ).attr({
               stroke:this.options.ticks.major.color?this.options.ticks.major.color:this.options.color
           });
            let text = thistickgroup.text(
                this.type?(xbase+this.options.ticks.major.size*(this.options.position==="right"?1:-1)):xbase,
                this.type?ybase:(ybase+this.options.ticks.major.size),
                ""+this.options.formatter(
                    this.minval+(
                        this.type?-(
                            this.graph.options.inner_height-ybase
                        )/this.scale:(xbase)/this.scale)
                )).attr({
                 //style:"display: block; transform: scale(-1,1)",
                 fill: this.options.color,
                'text-anchor':this.type?(this.options.position==="right"?"start":"end"):"middle",
                'dominant-baseline':this.type?"middle":"hanging",
            });

            rightspace = Math.max(rightspace,text.getBBox().x2);
            leftspace = Math.min(leftspace,text.getBBox().x);
            topspace = Math.min(topspace,text.getBBox().y);
            bottomspace = Math.max(bottomspace,text.getBBox().y2);
        }

        vb.x=Math.min(vb.x,leftspace-5);
        vb.y=Math.min(vb.y,topspace-5);
        vb.width=Math.max(vb.width,rightspace-vb.x+10);
        vb.height=Math.max(vb.height,bottomspace-vb.y+10);

        this.graph.svg.attr("viewBox",vb);

    }

    remove(){
        this.svg.remove();
        for(let ds in this.datasets){
            this.graph.remove_dataset(ds,false)
        }
    }

    checkscale(redraw=true){
        let maxval=-Infinity;
        let minval=Infinity;

       for(let i=0;i<this.datasets.length;i++){
           maxval=Math.max(maxval,this.type?this.datasets[i].maxy:this.datasets[i].maxx);
           minval=Math.min(minval,this.type?this.datasets[i].miny:this.datasets[i].minx);
       }
       if(maxval === minval || Math.abs(maxval*minval) === Infinity || isNaN(maxval*minval)){
           if(isNaN(maxval))
               maxval=0;
           if(isNaN(minval))
               minval=0;
           maxval=Math.max(maxval,0);
           minval=Math.min(minval,0);
           if(maxval === minval){
               maxval=1;
           }
       }
       var length = this.type?(parseInt(this.axis_line.attr('y2'))-parseInt(this.axis_line.attr('y1'))):(parseInt(this.axis_line.attr('x2'))-parseInt(this.axis_line.attr('x1')));
       var scale=length/(maxval-minval);
       if(scale !== this.scale || this.maxval !== maxval || this.minval!==minval) {
           this.maxval=maxval;
           this.minval=minval;
           this.scale = scale;
           for (let i = 0; i < this.datasets.length; i++) {
               this.datasets[i].redraw();
           }
       }
        if(redraw) {
            this.redraw();
        }
    }
}

class SVGGDataSet {
    constructor(svgGraph,name,options) {
        this.svg=svgGraph.svg.group().attr({
            groupe_type:"dataset",
            id:"dataset_"+name,
        });

        this.options={
            color:"#000000",
            autoscale:true,
            stroke_width:4,
            xAxis:svgGraph.xAxes[0],
            yAxis:svgGraph.yAxes[0],
        };
        this.options = update_json(this.options,options);
        this.x=[];
        this.y=[];
        this.lable=name;
        this.minx=Infinity;
        this.miny=Infinity;
        this.maxx=-Infinity;
        this.maxy=-Infinity;
        this.polyline=this.svg.polyline().attr({
            stroke:this.options.color,
            fill:"none",
            "stroke-width":this.options.stroke_width
        });
        this.setxAxis(options.xAxis);
        this.setyAxis(options.yAxis);
    }
    setxAxis(xAxis){
        if(typeof this.xAxis !== "undefined")
            this.xAxis.remove_dataset(this);
        this.xAxis=xAxis;
        this.xAxis.add_dataset(this);
    }
    setyAxis(yAxis){

        if(typeof this.yAxis !== "undefined")
            this.yAxis.remove_dataset(this);
        this.yAxis=yAxis;
        this.yAxis.add_dataset(this);
    }
    add_data(x,y,redraw=true){
        this.x.push(x);
        this.y.push(y);
        this.minx=Math.min(this.minx,x);
        this.maxx=Math.max(this.maxx,x);
        this.miny=Math.min(this.miny,y);
        this.maxy=Math.max(this.maxy,y);
        this.yAxis.checkscale(redraw);
        this.xAxis.checkscale(redraw);
    }

    redraw(){

        let x1 = parseInt(this.xAxis.axis_line.attr("x1"));
        let y1 = parseInt(this.yAxis.axis_line.attr("y1"));
        this.polyline.attr({
            points:
                this.x.map(function (x, i) {
                    return [x1+(x-this.xAxis.minval)*this.xAxis.scale, y1+(this.y[i]-this.yAxis.minval)*this.yAxis.scale];
                }.bind(this)).flat()
        })
    }
}

class SVGGraph {
    constructor(id, options={}) {
        this.svg = Snap("#" + id);
        //this.svg.attr({preserveAspectRatio :"xMidYMin slice"});
        this.datasets = {};
        this.options={
            inner_width:svggraph_defaults.resolution,
            inner_height:svggraph_defaults.resolution,
            autofit:true,
            background: svggraph_defaults.background,
            resolution:svggraph_defaults.resolution,
            resizable:true,
            legend:true
        };
        this.options = update_json(this.options,options);
        this.yAxes=[];
        this.xAxes=[];
        this.redraw();

        this.plotcolors=[
            '#1f77b4',  // muted blue
            '#ff7f0e',  // safety orange
            '#2ca02c',  // cooked asparagus green
            '#d62728',  // brick red
            '#9467bd',  // muted purple
            '#8c564b',  // chestnut brown
            '#e377c2',  // raspberry yogurt pink
            '#7f7f7f',  // middle gray
            '#bcbd22',  // curry yellow-green
            '#17becf'   // blue-teal
        ];
        this.add_axis("x");
        this.add_axis("y");
        this.redraw();
        this.resizable(this.options.resizable)
    }

    redraw(){
        if(this.options.autofit) {
            this.options.inner_width = this.svg.attr("width") * this.options.resolution;
            this.options.inner_height = this.svg.attr("height") * this.options.resolution;
        }
        this.svg.attr({
            viewBox: 0+","+0+","+this.options.inner_width+","+this.options.inner_height,
            style: 'background-color: '+this.options.background,
        });

        for(let i =0;i<this.yAxes.length;i++)
            this.yAxes[i].checkscale();
        for(let i =0;i<this.xAxes.length;i++)
            this.xAxes[i].checkscale();
        for(let ds in this.datasets)
            this.datasets[ds].redraw();
    }

    add_dataset(name,yaxis="y0",xaxis="x0") {
        if (this.getAxis(xaxis) === null){
            xaxis = this.add_axis("x", xaxis);}
        else{
            xaxis = this.getAxis(xaxis);
        }
        if (this.getAxis(yaxis) === null) {
            yaxis = this.add_axis("y", yaxis);
        }else {
            yaxis = this.getAxis(yaxis);
        }
        this.datasets[name]=new SVGGDataSet(
            this,name,
            {
                color:this.plotcolors[Object.keys(this.datasets).length%this.plotcolors.length],
                xAxis:xaxis,
                yAxis:yaxis,
            });
        if(xaxis !== this.xAxes[0])
            xaxis.color_as_dataset(0);
        if(yaxis !== this.yAxes[0])
            yaxis.color_as_dataset(0);
        return this.datasets[name];
    }

    remove_dataset(name,with_axis=true) {
        if(typeof this.datasets[name] === "undefined")return;
        this.datasets[name].options.xAxis.remove_dataset(this.datasets[name]);
        this.datasets[name].options.yAxis.remove_dataset(this.datasets[name]);
        this.datasets[name].svg.remove();

        if(with_axis) {
            if (this.datasets[name].options.xAxis.datasets.length === 0 && this.datasets[name].options.xAxis !== this.xAxes[0]) {
                this.remove_axis(this.datasets[name].options.xAxis);
            }
            if (this.datasets[name].options.yAxis.datasets.length === 0 && this.datasets[name].options.yAxis !== this.yAxes[0]) {
                this.remove_axis(this.datasets[name].options.yAxis);
            }
        }
        delete this.datasets[name];
    }

    add_data(dataset, x, y,redraw=true) {
        if (typeof this.datasets[dataset] === "undefined")
            this.add_dataset(dataset);

        this.datasets[dataset].add_data(x,y,redraw)
    }

    clear(){
        for(let ds in this.datasets){
            this.remove_dataset(ds)
        }
    }

    resizable(bool){
        if(bool){
            if (typeof jQuery.ui !== 'undefined'){
                $(this.svg.node).parent().width(this.svg.attr("width"));
                $(this.svg.node).parent().height(this.svg.attr("height"));
                $(this.svg.node).parent().resizable({
                    resize: function( event, ui ) {
                        this.svg.attr("width",ui.size.width);
                        this.svg.attr("height",ui.size.height);
                        this.redraw();
                    }.bind(this)
                });
            }else {

            }
        }
        else{
            if (typeof jQuery.ui !== 'undefined'){
                $(this.svg.node).parent().resizable("destroy");
            }
        }
    }

    add_axis(type,name=null) {
        if(type !== "x" && type !== "y")
            throw ("unknown axis type("+type+"), please choose x or y");

        var axisarray=null;
        if(type === "x")
            axisarray = this.xAxes;
        if(type === "y")
            axisarray = this.yAxes;

        if(name === null){
            var n=0;
            for(let i=0;i<axisarray.length;i++){
                let j = parseInt(axisarray[i].name.replace(type,""));
                if(j>=n){
                    n=j+1;
                }
            }
            name = type+""+n
        }
        let ax = new SVGGraphAxis(type,this,name);
        axisarray.push(ax);
        return ax
    }
    remove_axis(axis){
        axis.remove();
        var index = this.xAxes.indexOf(axis);
        if (index > -1) {
            this.xAxes.splice(index, 1);
        }
        index = this.yAxes.indexOf(axis);
        if (index > -1) {
            this.xAxes.splice(index, 1);
        }
    }

    getAxis(name) {
        for(let i=0;i<this.xAxes.length;i++){if (this.xAxes[i].name === name) return this.xAxes[i]}
        for(let i=0;i<this.yAxes.length;i++){if (this.yAxes[i].name === name) return this.yAxes[i]}
        return null
    }

    has_dataset(key) {
        return (typeof this.datasets[key] !== "undefined")
    }


}