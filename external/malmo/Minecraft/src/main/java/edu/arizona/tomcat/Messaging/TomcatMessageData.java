package edu.arizona.tomcat.Messaging;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import edu.arizona.tomcat.Mission.gui.RichContent;
import io.netty.buffer.ByteBuf;
import io.netty.buffer.ByteBufInputStream;
import io.netty.buffer.ByteBufOutputStream;

public class TomcatMessageData {
	
	private static enum Key { MISSION_PHASE_INSTRUCTIONS, MISSION_PHASE_MESSAGE, MISSION_PHASE_MESSAGE_DURATION };

	private Map<String, String> data;
	private RichContent richContent;
	
	/**
	 * Constructor
	 */
	public TomcatMessageData() {
		this.data = new HashMap<String, String>();
	}
	
	/**
	 * Constructor
	 * @param richContent - Rich content object
	 */
	public TomcatMessageData(RichContent richContent) {
		this.data = new HashMap<String, String>();
		this.richContent = richContent;
	}
	
	/**
	 * Reads the .json content of a buffer and loads it to the attributes of this class
	 * @param buffer - ByteBuffer object
	 * @throws IOException
	 */
	public void readDataFromBuffer(ByteBuf buffer) throws IOException {
		Gson gson = new Gson();        
        TomcatMessageData messageData = gson.fromJson(this.readStringFromByteBuffer(buffer), TomcatMessageData.class);
		this.data = messageData.data;
		this.richContent = messageData.richContent;
	}
	
	/**
	 * Convert the attributes of this class to a .json string and write it to the buffer
	 * @param buffer - ByteBuffer object
	 * @throws IOException
	 */
	public void writeDataToBuffer(ByteBuf buffer) throws IOException {
		Gson gson = new GsonBuilder().create();
        String json = gson.toJson(this);
		this.writeStringToByteBuffer(json, buffer);		
	}
	
	/**
	 * Writes a string to a ByteBuffer object
	 * @param string - String
	 * @param buffer - ByteBuffer object
	 * @throws IOException
	 */
	private void writeStringToByteBuffer(String string, ByteBuf buffer) throws IOException {			
		ByteBufOutputStream byteBufOutputStream = new ByteBufOutputStream(buffer);
		byteBufOutputStream.writeUTF(string);
		byteBufOutputStream.close();			
	}
	
	/**
	 * Reads a string from a ByteBuffer object
	 * @param buffer - ByteBuffer object
	 * @return
	 * @throws IOException
	 */
	private String readStringFromByteBuffer(ByteBuf buffer) throws IOException {			
		ByteBufInputStream byteBufInputStream = new ByteBufInputStream(buffer);
		String string =  byteBufInputStream.readUTF();
		byteBufInputStream.close();
		return string;
	}
	
	/**
	 * Adds a mission phase message to the data map
	 * @param message - Mission phase message
	 */
	public void setMissionPhaseMessage(String message) {
		this.data.put(Key.MISSION_PHASE_MESSAGE.toString(), message);
	}
	
	/**
	 * Retrieves a mission phase message from the data map
	 * @return
	 */
	public String getMissionPhaseMessage() {
		return this.data.get(Key.MISSION_PHASE_MESSAGE.toString());
	}
	
	/**
	 * Retrieves a rich content included in the message
	 * @return
	 */
	public RichContent getRichContent() {
		return this.richContent;
	}
	
}
