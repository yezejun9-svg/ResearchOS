package main

import (
	"context"
	"errors"
	"net"
	"time"
)

type socketTuple struct {
	clientIP, serverIP     [4]byte
	clientPort, serverPort uint16
}
type tcpOwnerRow struct {
	state                 uint32
	localIP, remoteIP     [4]byte
	localPort, remotePort uint16
	pid                   uint32
}
type connectionProof struct {
	dial  func(context.Context, string, string) (net.Conn, error)
	rows  func(socketTuple) ([]tcpOwnerRow, error)
	owned func(context.Context, uint32) error
}

func actualTuple(c net.Conn) (socketTuple, error) {
	var t socketTuple
	local, lok := c.LocalAddr().(*net.TCPAddr)
	remote, rok := c.RemoteAddr().(*net.TCPAddr)
	if !lok || !rok || local.IP.To4() == nil || remote.IP.To4() == nil || !local.IP.Equal(net.IPv4(127, 0, 0, 1)) || !remote.IP.Equal(net.IPv4(127, 0, 0, 1)) || remote.Port != 43861 || local.Port < 1 || local.Port > 65535 {
		return t, errors.New("actual socket tuple outside exact declared endpoint")
	}
	copy(t.clientIP[:], local.IP.To4())
	copy(t.serverIP[:], remote.IP.To4())
	t.clientPort = uint16(local.Port)
	t.serverPort = uint16(remote.Port)
	return t, nil
}
func establishedPID(t socketTuple, rows []tcpOwnerRow) (uint32, error) {
	var pid uint32
	matches := 0
	for _, r := range rows {
		if r.state == 5 && r.localIP == t.serverIP && r.remoteIP == t.clientIP && r.localPort == t.serverPort && r.remotePort == t.clientPort {
			matches++
			pid = r.pid
		}
	}
	if matches != 1 || pid == 0 {
		return 0, errors.New("server ESTABLISHED owner absent or ambiguous for actual tuple")
	}
	return pid, nil
}

// The transport cannot receive this connection until proof completes. Therefore
// no HTTP bytes can be written to an unproved/replacement listener. There is no
// LISTENER snapshot accepted as authority for this concrete connection.
func (p connectionProof) DialContext(ctx context.Context, network, address string) (net.Conn, error) {
	if (network != "tcp" && network != "tcp4") || address != "127.0.0.1:43861" {
		return nil, errors.New("dial outside declared endpoint")
	}
	c, e := p.dial(ctx, "tcp4", address)
	if e != nil {
		return nil, e
	}
	accepted := false
	defer func() {
		if !accepted {
			c.Close()
		}
	}()
	t, e := actualTuple(c)
	if e != nil {
		return nil, e
	}
	rows, e := p.rows(t)
	if e != nil {
		return nil, e
	}
	pid, e := establishedPID(t, rows)
	if e != nil {
		return nil, e
	}
	if e = p.owned(ctx, pid); e != nil {
		return nil, e
	}
	if e = ctx.Err(); e != nil {
		return nil, e
	}
	accepted = true
	return c, nil
}
func defaultDial(ctx context.Context, network, address string) (net.Conn, error) {
	return (&net.Dialer{Timeout: 5 * time.Second}).DialContext(ctx, network, address)
}
