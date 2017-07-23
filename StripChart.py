from Tkinter import*
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import matplotlib.animation as animation
import socket
import struct
import time
import datetime

messagetext =''

#counter for screenshots
shotcount = 0

#End of Data Flag - Set to 0, if Set to 1 = No More Data Coming
eodflag = '0'
timescale = 0.000256 #seconds
datafreq = int(round(1/timescale,-3))
#initialchartwidth is number of data sets displayed on the chart
initialchartwidth = 3*datafreq  #approximately 3 seconds of data 3*round(1/timescale,-3)  
#chartwith is number of data set display after zooming
chartwidth = initialchartwidth
#limit of data set that can be received
datalimits = 6000000  #max number of data sets to chart, 25 minutes @ 256usec  (
#array of zeros used to hold time axis data
tdata = [0 for x in range(datalimits)]  


#displayinc is increment of number of points display moves each animation
displayinc = int(initialchartwidth/6)
#startdisplayinc holds original value of displayinc
startdisplayinc = displayinc
#dinc is number of data points read each animation step
dinc = int(datafreq/2)  #approx 1/2 second of data or round(1/timescale,-3)/2
#refreshrate controls rate of animation in milliseconds
refreshrate = dinc/4  #every 1/2 second
#zuum is percent of chart zoom
zuum = 100


#.....................Display Control Functions call by Buttons.............

#save figure in file
def screenshot():
    global messagetext
    messagetext = "Saving Chart Frame..."
    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d_%H%M%S')
    shot = 'frame'+st+'.pdf'
    fig.savefig(shot)
    
#rewind data function called by rewind button
def rewind():
    global dmax
    global displayinc
    global displaymin
    global chartwidth
    global displaymax
    global messagetext
    messagetext = "Rewound first frame..."
    displayinc = 0
    displaymin = 0
    if dmax > chartwidth:
        displaymax = chartwidth
    else:
        displaymax = dmax
        
        
#fast backward function
def fback():
    global displayinc
    global startdisplayinc
    global zuum
    global messagetext
    messagetext = "Moving Backward Fast..."
    displayinc = int(-10*startdisplayinc*100/zuum)

#backward function
def back():
    global displayinc
    global startdisplayinc
    global zuum
    global messagetext
    messagetext = "Moving Backwards...."
    displayinc = int(-1*startdisplayinc*100/zuum)
   
#stop function: freezes display of data and chart
def stop():
    global displayinc
    global messagetext
    messagetext = "Strip Chart Stopped...."
    displayinc = 0
    
#forward at normal increment 
def forward():
    global displayinc
    global startdisplayinc
    global zuum
    global messagetext
    messagetext = "Moving Forward...."
    displayinc = int(startdisplayinc*100/zuum)
        
#fast forward
def fforward():
    global displayinc
    global startdisplayinc
    global zuum
    global messagetext
    messagetext = "Fast Forward...."
    displayinc = int(10*startdisplayinc*100/zuum)


#skip to realtime data position
def skipend():
    global displaymax
    global displaymin
    global chartwidth
    global displayinc
    global startdisplayinc
    global zuum
    global dmax
    global messagetext
    messagetext = "Skip Forward to Current Time..."
    displayinc = int(startdisplayinc*100/zuum)
    displaymax = dmax
    displaymin = displaymax - chartwidth
    if displaymin <= 1:
        displaymin = 1

#zoom 2x
def zoom():
    global chartwidth
    global initialchartwidth
    global zuum
    global displayinc
    global messagetext
    messagetext = "Zooming in +2X..."
    if chartwidth > 0.005 * initialchartwidth:
        chartwidth = chartwidth/2
        zuum = zuum * 2
        displayinc = int(displayinc/2)
        

#zoom 1/2x
def zoomout():
    global chartwidth
    global initialcartwidth
    global zuum
    global displayinc
    global messagetext
    messagetext = "Zooming out 1/2X...."
    chartwidth = chartwidth*2
    zuum  = int(zuum/2)

    
 
#zoom extents
def extents():
    global chartwidth
    global initialchartwidth
    global displayinc
    global zuum
    global messagetext
    messagetext = "Reset Zoom to 1X....."
    chartwidth = initialchartwidth
    displayinc = startdisplayinc
    zuum = 100

#jump to TOF
def jumptof(en):
    global displayinc
    global chartwidth
    global displaymax
    global dmax
    global tdata
    global messagetext
    
        
    content = entry.get()
    dhold = 0
    try:
        midchart = float(content)
        entry.delete(0,END)
        for i in range(0, dmax):
            searchtdata = tdata[i]
            if searchtdata > midchart:
                dhold = i
                break
        displaymax = int(dhold + chartwidth/2)
        displayinc = 0
        messagetext = "Jumping to "+str(midchart)+" ....."
        
    except ValueError:
        print "Not a float"

        


#------------------!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!----------------------------
#For demo purpose.  Read channel names from text file, 'Channel Names.txt' 
#Defines data order and channels recieved via socket

with open('ChannelNames.txt', 'r') as namesfile:
    #read channel names from file as string
    namedata=namesfile.read()
    #parse into a list
    names = namedata.strip().split(',')
    #print names
    #number of channel is number of items in list
    numchannel = len(names)
    #create array for actual data and fill with 0's
    channeldata = [[0 for x in range(datalimits)] for y in range(numchannel)]
#--------------------------------------------------------------------------------------------

#array of zeros used to hold min & max channel data with TOF
minchannel = [0 for x in range(numchannel)]
tminchannel = [0 for x in range(numchannel)]
maxchannel = [0 for x in range(numchannel)]
tmaxchannel = [0 for x in range(numchannel)]

#pre-set min max values
for i in range(0,numchannel):    
    minchannel[i] = 1000000.0
    maxchannel[i] = -1000000.0
    tminchannel[i] = 0
    tmaxchannel[i] = 0   

#..................Define and open socket..................
TCP_IP = '127.0.0.1'
TCP_PORT = 8889
BUFFER_SIZE = 4*(numchannel+1)  # Change to match bytes in each data package
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(1)
conn, addr = s.accept()


#..................define Tk object for data text........................
# define root window
bgkolor = 'lightgrey'
root = Tk()
root.configure(background=bgkolor, width = 2000)

#set title
root.title('Strip Chart')

checks = {}
for i in range(0,numchannel):
    checks[names[i]]='1'
   
#define first frame for radio buttons
row1 = Frame(root,height = 2, width = 4, background=bgkolor)
row1.pack()

for cname in names:
    checks[cname] = Variable()
    checks[cname].set('1')
    c = Checkbutton(row1, text=cname, variable=checks[cname],font=("Arial",9))
    c.pack(side ='left')

#define second frame for zoom buttons
row2 = Frame(root,height = 2, width = 4, background=bgkolor)
row2.pack()

#create zoom in button
zoomb = Button(row2, text="->In<-", command=zoom, font=("Arial",9))
#place zoom in button
zoomb.pack(side = 'left', fill='both', expand=True, padx=4)
#create zoom out button
zoomb = Button(row2, text="<-Out->", command=zoomout, font=("Arial",9))
#place zoom out button
zoomb.pack(side = 'left',fill='both', expand=True, padx=4)
#create zoom extents button
extentsb = Button(row2, text="|<100%>|", command=extents, font=("Arial",9))
#place zoom extents button
extentsb.pack(side = 'left',fill='both', expand=True, padx=4)

#define third frame for controls buttons
row3 = Frame(root,height = 2, width = 4, background=bgkolor)
row3.pack()

#create and place rewind button
screenshotb = Button(row3, text="Save Frame", command=screenshot, font=("Arial",9))
screenshotb.pack(side = 'left')
#create and place rewind button
rewindb = Button(row3, text="|<", command=rewind, font=("Arial",9))
rewindb.pack(side = 'left')
#create and place fast backward button
fbackb = Button(row3, text="<<", command=fback, font=("Arial",9))
fbackb.pack(side = 'left')
#create and place backward button
backb = Button(row3, text="<-", command=back, font=("Arial",9))
backb.pack(side = 'left')
#create and place stop button
stopb = Button(row3, text="STOP", command=stop, font=("Arial",9))
stopb.pack(side = 'left')
#create and place forward button
forwardb = Button(row3, text="->", command=forward, font=("Arial",9))
forwardb.pack(side = 'left')
#create and place fast forward button
fforwardb = Button(row3, text=">>", command=fforward, font=("Arial",9))
fforwardb.pack(side = 'left')
#create and place skip to end button
skipendb = Button(row3, text=">|", command=skipend, font=("Arial",9))
skipendb.pack(side = 'left')
#create and place Jump to input box
jumplabel = Label(row3, text = "Jump TOF: ", font=("Arial",9))
jumplabel.pack(side = 'left')
entry = Entry(row3, width = 10, font=("Arial",9))
entry.pack(side = 'left')
entry.bind('<Return>', jumptof)

#define fourth frame for system messages
row4 = Frame(root,height = 1, width = 60, background=bgkolor)
row4.pack()
mtext = Text(row4, width = 40, height = 1, background = bgkolor,font=("Arial",8))
mtext.pack()


#set text box size
btext = Text(root, width = 30, height = numchannel*3+3, background = bgkolor,font=("Arial",8))
#pack to show box
btext.pack(side ='left',padx=10)



# create canvas for chart
chartcanvas = Canvas(root, width=600, height=400, background =bgkolor)
chartcanvas.pack(side = 'left')
#........................define figure for chart.....................   
fig = plt.figure(facecolor = bgkolor)
fig.set_size_inches(11, 8, forward=True)
#set chart title
fig.canvas.set_window_title('Telemetry')
#add primary y axis to chart
ax1 = fig.add_subplot(1,1,1, axisbg=bgkolor)



canvas = FigureCanvasTkAgg(fig, chartcanvas)
canvas.show()
canvas.get_tk_widget().pack(side='left', fill=BOTH, expand=True)

#counter for data lines recieved first line
dcount = 0
dmax = 0
displaymin = 0 #lowest value displayed on x-axis of chart.
displaymax = 0 #highest value displayed on x-axis of chart.
mcount = 0
  
def animate(i):
    #make some variables global
    global displayinc
    global dinc
    global displaymin
    global displaymax
    global chartwidth
    global tdata
    global tmax
    global dmax
    global channeldata
    global btext
    global names
    global zuum
    global numchannel
    global dcount
    global eodflag
    global messagetext
    global mcount


    
    #get next "dinc" data points
    #test for end of data flag
    if eodflag != '1':
        for i in range(0,dinc):
            data = conn.recv(BUFFER_SIZE)
            #no more data coming, shut down socket and data recieve loop
            if not data:
                eodflag = '1'
                s.close()
                dinc = 0
                messagetext = '>>>>REALTIME DATA ENDED<<<<<\n'
                print 'eod recieved'
                break
            num = numchannel+1
            packet = struct.unpack('f'*num,data)
            tdata[dcount+i] = packet[0]
            tmax =  tdata[dcount+i]
            dmax = dcount+i
            for n in range(0,numchannel):
                channeldata [n][dcount+i] = packet[n+1]
                if channeldata[n][dcount+i] < minchannel[n]:
                    minchannel[n] = channeldata[n][dcount+i]
                    tminchannel[n] = tdata[dcount+i]                    
                else:
                    if channeldata[n][dcount+i] > maxchannel[n]:
                        maxchannel[n] = channeldata[n][dcount+i]
                        tmaxchannel[n] = tdata[dcount+i]
            conn.send(str(tmax))  
    dcount = dcount + dinc

    
    #move displayinc frames.  Note displayinc can be negative
    displaymax = displaymax + displayinc
    
    #check display values are valid    
    if displaymax>dmax:
        displayinc = int(startdisplayinc*100/zuum)
        displaymax = dmax
    displaymin = displaymax - chartwidth
            
    if dcount > 1:
        if displaymin < 0:
            displaymin = 0
   
    if displaymax <= 0:
        displaymax = 0
        displayinc = startdisplayinc

    #Update text window
    #clear text window for next data set to be displayed
    btext.delete('1.0', END)    

    #show TOF
    wtext = "Realtime TOF: "+str(round(tmax,2))+' msec \n'
    btext.insert(INSERT, wtext)
   
    #value of end of x-axis  
    wtext = "Chart Max: "+str(round(tdata[displaymax],2))+' msec \n'
    btext.insert(INSERT, wtext)

    
    for i in range(0,numchannel):
        if checks[names[i]].get()=='1':
            wtext = names[i]+':\n'
            btext.insert(INSERT, wtext)
            tmaxstr =''
            tmaxstr = str(round(tmaxchannel[i],2))
            maxstr = ''
            maxstr = str(round(maxchannel[i],2))
            wtext = 'Max: '+ maxstr +' TOF: '+ tmaxstr+'\n'
            btext.insert(INSERT, wtext)
            tminstr = ''
            tminstr = str(round(tminchannel[i],2))
            minstr = ''
            minstr = str(round(minchannel[i],2))
            wtext = 'Min: '+ minstr +' TOF: '+ tminstr+'\n'
            btext.insert(INSERT, wtext)


    #Update message window
    #clear message window for next data set to be displayed
    mtext.delete('1.0', END)
    #this loop allow message to linger for reading with blocking other loops
    if mcount <10:
        mtext.insert(INSERT, messagetext)
        mcount = mcount+1
    else:
        mcount = 0
        messagetext =''

    #update box display        
    root.update()
     
    #Update chart
    ax1.clear()
    #ax2.clear()
    if displaymax >= chartwidth:
            tplot = tdata[displaymin:displaymax]
            for i in range(0, numchannel):
                if checks[names[i]].get()=='1':
                    channel = channeldata[i][displaymin:displaymax]
                    ax1.plot(tplot,channel, label = names[i])
 
    else:
            #special case if data recieved is less than chartwidth
            tplot = tdata[0:displaymax]
            for i in range(0, numchannel):
                if checks[names[i]].get()=='1':
                    channel = channeldata[i][0:displaymax]
                    ax1.plot(tplot,channel, label = names[i])
       
    #set up y axis legend                
    handles, labels = ax1.get_legend_handles_labels()
    #set legend location and font size
    ax1.legend(loc=3, shadow=True, fontsize='xx-small')

    #set chart title and fontsize
    plt.title('Realtime Data', fontsize = "small")
    #set axis label font sizes
    ax1.tick_params(labelsize='xx-small')
    #ax2.tick_params(labelsize='xx-small')

    ax1.yaxis.grid(color='black', linestyle='dashed')
    ax1.xaxis.grid(color='black', linestyle='dashed')

    #label each axis

    ax1.set_ylabel('IMU Data')
    ax1.set_xlabel('TOF msec')

    
#interval = refreshrate = time in milliseconds each animation cycle
#note:  number of data set read each interval is set by 'dinc' variable    
ani = animation.FuncAnimation(fig, animate, interval=refreshrate)
root.mainloop()
              
            
   


    
  


               

               


