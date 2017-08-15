from Tkinter import*
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
#from matplotlib.figure import Figure
import matplotlib.animation as animation
import socket
import struct
import time
import datetime
import pickle
import collections

class StripChart:
    
    #============================Setup and Initialization Section=============================================
    
    def __init__(self):
        #...........DEMO ONLY.....text file with channel names
        self.filename = ''
        #max number of data sets to chart, 25 minutes @ 256usec
        self.datalimits = 650000 #approx 6 hours of data @ 10 hz
        #approximate period of time between data sets...only used to estimate chartwidth and other pre-sets
        self.timescale = 0.1 #seconds
        #datafreq is frequency of data sets in hz
        self.datafreq = int(round(1/self.timescale,-1))
        #self.initialchartwidth is number of data sets displayed on the chart
        self.initialchartwidth = 3*self.datafreq  #approximately 3 seconds of data 
        #chartwith is number of data sets displayed after zooming
        self.chartwidth = self.initialchartwidth
        #self.dinc is number of data points read each animation step
        self.dinc = int(self.datafreq/2)  #approx 1/2 second of data
        if self.dinc < 1:
            self.dinc =1
        #self.displayinc is increment of number of points display moves each animation
        self.displayinc = self.dinc
        #startself.displayinc holds original value of self.displayinc, self.displayinc can be modified by zuum function
        self.startdisplayinc = self.displayinc    
        #refreshrate controls rate of animation in milliseconds
        self.refreshrate = 10 #set to small number to make data recieve control speed
        #used to clip data to fit chartwidth
        #displaymin is lowest data set NUMBER, not tdata value to be displayed
        self.displaymin =0
        #displaymmax is highes data set NUMBER, not tdata value to be displayed
        self.displaymax = 0
        #limit of data set that can be received
        self.tdata = [0 for x in range(self.datalimits)]
        #maximum value of tdata recieved
        self.tmax =0
        #maximum number of data sets recieved
        self.dmax =0
        #counter for data sets recieved so far
        self.dcount =0
        #End of Data Flag - Set to 0, if Set to 1 = No More Data Coming
        self.eodflag = '0'
        #Feedback message to display for events like button pushed
        self.messagetext =''
        #message counter, allows messagetext to linger so user can read it before it is erased
        self.mcount = 0
        #strings used in text box 
        self.maxstr =''
        self.minstr=''
        self.tmaxstr=''
        self.tminstr=''

    #open  socket for tof and channel data
    def opensock(self,port):
        #..................Define and open socket..................
        self.TCP_IP = '127.0.0.1'
        self.TCP_PORT = port
        self.BUFFER_SIZE = 1024  
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind((self.TCP_IP, self.TCP_PORT))
        self.s.listen(1)
        self.conn, self.addr = self.s.accept()

    #gets channel names and setup balance of variables....
    def getnames(self):
        #..........This is a demo solution...actual channel names may be pass in a different way....
        self.dict = collections.OrderedDict()
        self.dict = pickle.loads(self.conn.recv(self.BUFFER_SIZE))
        #make list of keys
        self.names= self.dict.keys()
        #first TOF data 
        self.tdata[0] = self.dict[self.names[0]]
        #remove first key which is TOF, so names is just list of channel names now
        self.names.pop(0)
        #number of channel is number of items in list
        self.numchannel = len(self.names)
        #create array for actual data and fill with 0's
        self.channeldata = [[0 for x in range(self.datalimits)] for y in range(self.numchannel)]
        #array of zeros used to hold min & max channel data with TOF
        self.minchannel = [0 for x in range(self.numchannel)]
        self.tminchannel = [0 for x in range(self.numchannel)]
        self.maxchannel = [0 for x in range(self.numchannel)]
        self.tmaxchannel = [0 for x in range(self.numchannel)]
        #pre-set min max values
        for i in range(0,self.numchannel):
            self.minchannel[i] = 1000000.0
            self.maxchannel[i] = -1000000.0
            self.tminchannel[i] = 0
            self.tmaxchannel[i] = 0
            self.channeldata[i][0] = self.dict[self.names[i]]
        #..................define Tk object for data text........................
        # define self.root window
        self.bgkolor = 'lightgrey'
        self.root = Tk()
        self.root.configure(background=self.bgkolor, width = 2000)

        #set title
        self.root.title('Strip Chart')

        self.checks = {}
        for i in range(0,self.numchannel):
            self.checks[self.names[i]]='1'
               
        #define first frame for radio buttons
        self.row1 = Frame(self.root,height = 2, width = 4, background=self.bgkolor)
        self.row1.pack()

        for cname in self.names:
            self.checks[cname] = Variable()
            self.checks[cname].set('1')
            c = Checkbutton(self.row1, text=cname, variable=self.checks[cname],font=("Arial",9))
            c.pack(side ='left')

        #define second frame for zoom buttons
        self.row2 = Frame(self.root,height = 2, width = 4, background=self.bgkolor)
        self.row2.pack()
        
        #create chart zoom slider
      
        self.zoomslider =Scale(self.row2,from_=0.1, to=10, sliderlength = 10, showvalue=  0, resolution = 0.1,length = 400, label = "<IN-----------------------------------ZOOM------------------------------Out---Ext's>",orient = HORIZONTAL)
        self.zoomslider.set(1)
        self.zoomslider.pack(side='left')


        #define third frame for speed slider
        self.row3 = Frame(self.root,height = 2, width = 4, background=self.bgkolor)
        self.row3.pack()
          
        #create chart speed slider
      
        self.speedslider =Scale(self.row3,from_=-10, to =10, sliderlength = 10, showvalue= 0, resolution = 0.2,length = 400, label = "<Reverse-------------------------Chart Speed--------------------------Forward>",orient = HORIZONTAL)
        self.speedslider.set(1)
        self.speedslider.pack(side='left')
   
        
        #define forth frame for control buttons
        self.row4 = Frame(self.root,height = 1, width = 60, background=self.bgkolor)
        self.row4.pack()

        #create and place screen shot button
        self.screenshotb = Button(self.row4, text="Save Frame", command=self.screenshot, font=("Arial",9))
        self.screenshotb.pack(side = 'left') 
        
        #create and place stop button
        self.stopb = Button(self.row4, text="|------------STOP-------------|", command=self.stop, font=("Arial",9))
        self.stopb.pack(side = 'left')
        
        #create and place Jump to input box
        self.jumplabel = Label(self.row4, text = "Jump TOF: ", font=("Arial",9))
        self.jumplabel.pack(side = 'left')
        self.entry = Entry(self.row4, width = 10, font=("Arial",9))
        self.entry.pack(side = 'left')
        self.entry.bind('<Return>', self.jumptof)

        #define fifth frame for system messages
        self.row5 = Frame(self.root,height = 1, width = 60, background=self.bgkolor)
        self.row5.pack()
        self.mtext = Text(self.row5, width = 65, height = 1, background = self.bgkolor,font=("Arial",8))
        self.mtext.tag_configure("center", justify='center')
        self.mtext.pack()


        #set text box size
        self.btext = Text(self.root, width = 25, height = self.numchannel*3+2, background = self.bgkolor,font=("Arial",8))
        #pack to show box
        self.btext.pack(side ='left',padx=5)

        #set Second text box size
        self.b2text = Text(self.root, width = 25, height = self.numchannel*3+2, background = self.bgkolor,font=("Arial",8))
        #pack to show box
        self.b2text.pack(side ='left',padx=5)


        # create self.canvas for chart
        self.chartcanvas = Canvas(self.root, width=600, height=400, background =self.bgkolor)
        self.chartcanvas.pack(side = 'left')
            
        #........................define figure for chart.....................   
        self.fig = plt.figure(facecolor = self.bgkolor)
        self.fig.set_size_inches(11, 8, forward=True)
        #set chart title
        self.fig.canvas.set_window_title('Telemetry')
        #add primary y axis to chart
        self.ax1 = self.fig.add_subplot(1,1,1, axisbg=self.bgkolor)

        self.canvas = FigureCanvasTkAgg(self.fig, self.chartcanvas)
        self.canvas.show()
        self.canvas.get_tk_widget().pack(side='left', fill=BOTH, expand=True)

        #counter for data lines recieved first line
        self.dcount = 0
        self.dmax = 0
        self.displaymin = 0 #lowest value displayed on x-axis of chart.
        self.displaymax = 0 #highest value displayed on x-axis of chart.
        self.mcount = 0

        #send string back to tell sender ready for more data
        self.conn.send('Setup Complete')


    #====================Action functions for buttons===============================
            
    #create plot file of chart..............
    def screenshot(self):
            ts = time.time()
            st = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d_%H%M%S')
            shot = 'frame'+st+'.pdf'
            self.messagetext = "............Saving filename: "+shot
            self.fig.savefig(shot)
    
    #stop function: freezes display of data and chart
    def stop(self):

        
        
        self.messagetext = "......Chart Stopped..........."
        self.displayinc = 0
        self.speedslider.set(0)

    #jump to TOF
    def jumptof(self,en):
       
        self.content = self.entry.get()
        self.dhold = 0
        try:
            self.midchart = float(self.content)
            self.entry.delete(0,END)
            for i in range(0, self.dmax):
                self.searchtdata = self.tdata[i]
                if self.searchtdata > self.midchart:
                    self.dhold = i
                    break
            self.displaymax = int(self.dhold + self.chartwidth/2)
            self.displayinc = 0
            self.speedslider.set(0)
            self.messagetext = "........Jumping to "+str(self.midchart)+" ....."
            
        except ValueError:
            self.messagetext = "........Not Valid Input..........."

    #========================MAIN LOOP ==========================================================

    def runanimation(self):

        #interval = refreshrate = time in milliseconds each animation cycle
        #note:  number of data set read each interval is set by 'self.dinc' variable    
        self.ani = animation.FuncAnimation(self.fig, self.animate, interval=self.refreshrate)
        #Tkinter mainloop, require to show window
        self.root.mainloop()

    #===========================Animation Function ===========================================      
    #animation function....this is main looping function that fills window with data, chart with lines each animation frame
    def animate(self,i):
        #This section reads in data each frame.....stops reading when EOD is detected
        #get next "self.dinc" data points
        #test for end of data, EOD, flag
        if self.eodflag != '1':
            for i in range(0,self.dinc):
                data =self.conn.recv(self.BUFFER_SIZE)
                #no more data coming, shut down socket and set eodflag
                if (not data) or (self.dmax >= self.datalimits-self.dinc):
                    self.eodflag = '1'
                    self.s.close()
                    self.dinc = 0
                    self.messagetext = '>>>>REALTIME DATA ENDED<<<<<\n'
                    print 'eod recieved'
                    break
                self.dict = pickle.loads(data)
                #TOF data 
                self.tdata[self.dcount+i] = self.dict['TOF']
                #reset current time
                self.tmax =  self.tdata[self.dcount+i]
                #reset current data count
                self.dmax = self.dcount+i
                #parse channel data from ordered dictionary  
                for n in range(0,self.numchannel):
                    self.channeldata[n][self.dcount+i] = self.dict[self.names[n]]
                    #set min & max each channel
                    if self.channeldata[n][self.dcount+i] < self.minchannel[n]:
                        self.minchannel[n] = self.channeldata[n][self.dcount+i]
                        self.tminchannel[n] = self.tdata[self.dcount+i]                    
                    else:
                        if self.channeldata[n][self.dcount+i] > self.maxchannel[n]:
                            self.maxchannel[n] = self.channeldata[n][self.dcount+i]
                            self.tmaxchannel[n] = self.tdata[self.dcount+i]
                self.conn.send(str(self.tmax))  
        self.dcount = self.dcount + self.dinc
        self.sspeed = self.speedslider.get()
        if (self.sspeed == 0) and (self.messagetext == ''):
                self.messagetext = '...........Chart Stopped...........'
        self.displayinc = int(float(self.startdisplayinc)*self.sspeed)
        self.displaymax = self.displaymax + self.displayinc


        #=========Chart Adjustsments and Scaling================================
        
        self.szoom = self.zoomslider.get()
        
        if self.szoom > 9.2:
            if self.displayinc <> 0:
                self.displayinc = self.startdisplayinc
                self.speedslider.set(1)
                self.displaymin = 0
                self.displaymax = self.dmax
            if self.messagetext == '':
                self.messagetext = '...........Zoomed Extents...........'
            self.chartwidth = self.dmax
        else:
            self.chartwidth = int(self.szoom*float(self.initialchartwidth))

        if self.chartwidth < 3:
            self.chartwidth = 3

        if (self.dcount > 1) and (self.displaymin < 0):
            self.displaymin = 0

        if (self.displaymax>self.dmax):
            self.displaymax = self.dmax
            self.speedslider.set(1)
            self.displayinc = self.startdisplayinc
            self.messagetext = '...........Chart Speed Adjusted..........'

        if self.displaymax < 0:
            self.displaymax = 0
            self.displayinc = self.startdisplayinc
            self.speedslider.set(1)
            self.messagetext = '...........Chart Speed Adjusted..........'

        self.displaymin = self.displaymax - self.chartwidth

        
        #=============Text Window Section =========================
        #Update text window
        #clear text window for next data set to be displayed
        self.btext.delete('1.0', END)
        self.b2text.delete('1.0', END)


        #show TOF
        self.wtext = 'Realtime TOF: '+str(round(self.tmax,2))+' msec \n'
        self.b2text.insert(INSERT, self.wtext)
       
        #value of end of x-axis  
        self.wtext = 'Chart Max: '+str(round(self.tdata[self.displaymax],2))+' msec \n'
        self.btext.insert(INSERT, self.wtext)

        
        for i in range(0,self.numchannel):
            if self.checks[self.names[i]].get()=='1':
                self.wtext = self.names[i]+':\n'
                self.btext.insert(INSERT, self.wtext)
                self.b2text.insert(INSERT, self.wtext)
                self.tmaxstr =''
                self.tmaxstr = str(round(self.tmaxchannel[i],2))
                self.maxstr = ''
                self.maxstr = str(round(self.maxchannel[i],2))
                self.wtext = 'Max: '+ self.maxstr +' TOF: '+ self.tmaxstr+'\n'
                self.btext.insert(INSERT, self.wtext)
                self.tminstr = ''
                self.tminstr = str(round(self.tminchannel[i],2))
                self.minstr = ''
                self.minstr = str(round(self.minchannel[i],2))
                self.wtext = 'Min: '+ self.minstr +' TOF: '+ self.tminstr+'\n'
                self.btext.insert(INSERT, self.wtext)
                self.wtext = "Last Rec'd: "+str(round(self.channeldata[i][self.dmax],2))+'\n\n'
                self.b2text.insert(INSERT, self.wtext)


        #Update message window
        #clear message window for next data set to be displayed
        self.mtext.delete('1.0', END)
        #this loop allow message to linger for reading with blocking other loops
        if self.mcount <10:
            self.mtext.insert(INSERT, self.messagetext)
            self.mtext.tag_add("center", 1.0, "end")
            self.mcount = self.mcount+1
        else:
            self.mcount = 0
            self.messagetext = ''
            

        #update box display        
        self.root.update()
        
        
        #==============================Plotting Data Section =========================        
        #Update chart
        self.ax1.clear()
    
        if self.displaymax >= self.chartwidth:
                tplot = self.tdata[self.displaymin:self.displaymax]
                for i in range(0, self.numchannel):
                    if self.checks[self.names[i]].get()=='1':
                        channel = self.channeldata[i][self.displaymin:self.displaymax]
                        self.ax1.plot(tplot,channel, label = self.names[i])
     
        else:
                #special case if data recieved is less than self.chartwidth
                tplot = self.tdata[0:self.displaymax]
                for i in range(0, self.numchannel):
                    if self.checks[self.names[i]].get()=='1':
                        channel = self.channeldata[i][0:self.displaymax]
                        self.ax1.plot(tplot,channel, label = self.names[i])
           
        #set up y axis legend                
        handles, labels = self.ax1.get_legend_handles_labels()
        #set legend location and font size
        self.ax1.legend(loc=3, shadow=True, fontsize='xx-small')

        #set chart title and fontsize
        plt.title('Realtime Data', fontsize = "small")
        #set axis label font sizes
        self.ax1.tick_params(labelsize='xx-small')
        #ax2.tick_params(labelsize='xx-small')

        self.ax1.yaxis.grid(color='black', linestyle='solid')
        self.ax1.xaxis.grid(color='black', linestyle='solid')

        #label each axis

        self.ax1.set_ylabel('IMU Data')
        self.ax1.set_xlabel('TOF msec')

         



        

